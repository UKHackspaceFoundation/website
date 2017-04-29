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

# get instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# utility functions:
def get_gocardless_client():
    return gocardless_pro.Client(
        access_token = getattr(settings, "GOCARDLESS_ACCESS_TOKEN", None),
        environment = getattr(settings, "GOCARDLESS_ENVIRONMENT", None)
    )


class GocardlessPaymentManager(models.Manager):
    # get_or_create that populates fields from json
    # e.g. as received from gocardless webhook or payment creation api
    # payload should be a dict, e.g. parsed from webhook json
    def get_or_create_from_payload(self, payload, mandate):
        try:
            # create with required fields only
            obj, created = super(GocardlessPaymentManager, self).get_or_create(
                id = payload.id,
                created_at = timezone.now(),
                amount = payload.amount,
                currency = payload.currency,
                status = payload.status
            )
            # update everything else in the payload
            for key, value in payload.__dict__.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            # don't forget the links
            if hasattr(payload.links, 'creditor') and payload.links.creditor is not None:
                obj.creditor_id = payload.links.creditor
            if hasattr(payload.links, 'payout') and payload.links.payout is not None:
                obj.payout_id = payload.links.payout

            # associate to mandate
            obj.mandate = mandate

            obj.save()
            return obj

        except Exception as e:
            logger.error("Error in GocardlessPaymentManager.get_or_create_from_payload - exception creating payment: " + repr(e), extra={'payload':payload})
            return None

    def process_payment_from_webhook(self, event, response):
        # best to ignore the event itself and just fetch latest status via the api
        # this is in case the webhook event is received out of order

        logger.info("Processing payment id:{}".format(event['links']['payment']))

        client = get_gocardless_client()

        # get latest payment info from api
        try:
            info = client.payments.get(event['links']['payment'])

            # get matching payment object from DB
            try:
                payment = super(GocardlessPaymentManager, self).get_queryset().get(id=event['links']['payment'])

                print(repr(info))

                # save changes to object - this will also trigger internal handling
                payment.status = info.status
                payment.charge_date = info.charge_date
                payment.save()

            except GocardlessPayment.DoesNotExist as e:
                # odd...  best to create a matching payment record for consistency
                logger.warning("Warning in GocardlessPaymentManager.process_payment_from_webhook - payment object not found: " + repr(e), extra={'event':event})

                # see if we have a matching mandate object:
                mandate = None
                try:
                    mandate = GocardlessMandate.objects.get(id=info['links']['mandate'])
                except GocardlessMandate.DoesNotExist as e:
                    logger.warning("Warning in GocardlessPaymentManager.process_payment_from_webhook - mandate object not found: " + repr(e), extra={'event':event})

                # create the payment record
                self.get_or_create_from_payload(info, mandate)


        except Exception as e:
            # odd - this should always be possible, perhaps there was a connection error
            logger.error("Error in GocardlessPaymentManager.process_payment_from_webhook - exception fetching payment info: " + repr(e), extra={'event':event})


        return response


class GocardlessPayment(models.Model):
    id = models.CharField(max_length=16, unique=True, primary_key=True)
    created_at = models.DateTimeField(default=timezone.now)
    charge_date = models.DateField(default=timezone.now, blank=True)
    amount = models.IntegerField(default=0)
    description = models.CharField(max_length=100, blank=True)
    currency = models.CharField(max_length=10)
    status = models.CharField(max_length=26)
    amount_refunded = models.IntegerField(default=0)
    reference = models.CharField(max_length=10, blank=True)
    payout_date = models.DateField(default=timezone.now, blank=True)
    creditor_id = models.CharField(max_length=16, blank=True)
    payout_id = models.CharField(max_length=16, blank=True)
    idempotency_key = models.CharField(max_length=33, blank=True)
    mandate = models.ForeignKey('GocardlessMandate', models.SET_NULL, blank=True, null=True)

    objects = GocardlessPaymentManager()

    class Meta:
        db_table = 'gocardlesspayment'
        app_label = 'main'

    def __init__(self, *args, **kwargs):
        super(GocardlessPayment, self).__init__(*args, **kwargs)
        self.old_status = self.status

    def save(self, force_insert=False, force_update=False):
        if self.status != self.old_status:
            # status has changed...  so need to act on it:

            # bubble status change event up to mandate

            pass


        super(GocardlessPayment, self).save(force_insert, force_update)
        self.old_status = self.status
