from django.db import models
from django.conf import settings
from django.contrib.auth.models import (AbstractUser,BaseUserManager)
from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import gocardless_pro
import logging
import uuid
from .gocardless_payment import GocardlessPayment

# get instance of a logger
logger = logging.getLogger(__name__)


# utility functions:
def get_gocardless_client():
    return gocardless_pro.Client(
        access_token = getattr(settings, "GOCARDLESS_ACCESS_TOKEN", None),
        environment = getattr(settings, "GOCARDLESS_ENVIRONMENT", None)
    )


class GocardlessMandateManager(models.Manager):

    # get all mandate records for supporter membership
    def get_mandate_history_for_supporter_membership(self, supporter_membership):
        return super(GocardlessMandateManager, self).get_queryset().filter(supporter_membership=supporter_membership)

    # get latest mandate for supporter_membership
    def get_mandate_for_supporter_membership(self, supporter_membership):
        return self.get_mandate_history_for_supporter_membership(supporter_membership).latest('created_at')

    # get latest mandate status for supporter_membership or throw DoesNotExist
    def get_membership_status_for_supporter_membership(self, supporter_membership):
        return self.get_mandate_for_supporter_membership(supporter_membership).status

    # get_or_create that populates fields from json
    # e.g. as received from gocardless webhook or mandate creation api
    # payload should be a dict, e.g. parsed from webhook json
    def get_or_create_from_payload(self, payload):
        try:
            # create with required fields only
            obj, created = super(GocardlessMandateManager, self).get_or_create(
                id = payload.id,
                created_at = timezone.now(),
                status = payload.status
            )
            # update everything else in the payload
            for key, value in payload.__dict__.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            # don't forget the links
            if hasattr(payload.links, 'customer') and payload.links.customer is not None:
                obj.customer_id = payload.links.customer
            if hasattr(payload.links, 'creditor') and payload.links.creditor is not None:
                obj.creditor_id = payload.links.creditor
            if hasattr(payload.links, 'customer_bank_account') and payload.links.customer_bank_account is not None:
                obj.customer_bank_account_id = payload.links.customer_bank_account

            obj.save()
            return obj

        except Exception as e:
            logger.error("Error in GocardlessMandateManager.get_or_create_from_payload - exception creating payment: " + repr(e), extra={'payload':payload})
            return None


class GocardlessMandate(models.Model):
    id = models.CharField(max_length=16, unique=True, primary_key=True)
    created_at = models.DateTimeField(default=timezone.now)
    reference = models.CharField(max_length=10, blank=True)
    status = models.CharField(max_length=26, blank=True)
    creditor_id = models.CharField(max_length=16, blank=True)
    customer_id = models.CharField(max_length=16, blank=True)
    customer_bank_account_id = models.CharField(max_length=16, blank=True)
    # which Supporter membership is this mandate associated with (or null)
    supporter_membership = models.ForeignKey('SupporterMembership', models.CASCADE, null=True)
    # which Space Membership is this mandate associated with (or null)
    # TODO: ^^

    # override default manager
    objects = GocardlessMandateManager()

    class Meta:
        db_table = 'gocardlessmandate'
        app_label = 'main'

    # is_supporter_mandate
    def is_supporter_mandate(self):
        return self.supporter_membership is not None

    # TODO: is_space_mandate

    # is_active - is this mandate active
    def is_active(self):
        return not (self.status == 'failed' or self.status == 'expired' or self.status == 'cancelled')

    def cancel(self):
        # get gocardless client object
        client = get_gocardless_client()

        try:
            # cancel mandate
            mandate = client.mandates.cancel(self.id)

            # update status (should be cancelled)
            self.status = mandate.status
            self.save()

            return True

        except Exception as e:
            logger.error("Error in GocardlessMandate.cancel: "+repr(e), extra={'mandate':self})
            return False


    # Get associated payments
    def get_payments(self):
        return GocardlessPayment.objects.filter(mandate=self)


    # Get latest payment (will throw DoesNotExist exception if none)
    def get_latest_payment(self):
        return self.get_payments().latest('created_at')


    def create_payment(self, amount):
        if not self.is_active():
            raise RuntimeError("Request to create_payment for an inactive mandate");

        # get gocardless client object
        client = get_gocardless_client()

        # generate idempotency key
        key = uuid.uuid4().hex

        try:
            # create payment
            payment = client.payments.create(
                params={
                    "amount" : int(amount * 100), # convert to pence
                    "currency" : "GBP",
                    "links" : {
                        "mandate": self.id
                    },
                    "metadata": {
                        "type":"SupporterSubscription"
                        # TODO: decide if we want to add metadata to the payment
                    }
                }, headers={
                    'Idempotency-Key' : key
            })

            # Store payment object
            payment.idempotency_key = key
            obj = GocardlessPayment.objects.get_or_create_from_payload(payment, self)

            return obj

        except Exception as e:
            logger.error("Error in GocardlessMandate.create_payment: "+repr(e), extra={'mandate':self})
            return None

    # called when webhook receives a payment associated with this mandate
    def handle_payment_updated(self, payment):
        # if paid_out, bubble up to supprter membership
        if payment.status == 'paid_out':
            if self.supporter_membership is not None:
                self.supporter_membership.handle_payment_received(payment)
