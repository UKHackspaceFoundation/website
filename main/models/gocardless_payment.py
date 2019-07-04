from django.db import models
from django.utils import timezone
import logging

from .gocardless import get_gocardless_client

# get instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GocardlessPaymentManager(models.Manager):
    # get_or_create that populates fields from json
    # e.g. as received from gocardless webhook or payment creation api
    # payload should be a dict, e.g. parsed from webhook json
    def get_or_create_from_payload(self, payload, mandate):
        try:
            # create with required fields only
            obj, created = super(GocardlessPaymentManager, self).get_or_create(
                id=payload.id,
                created_at=timezone.now(),
                amount=payload.amount,
                currency=payload.currency,
                status=payload.status
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

        except Exception:
            logger.exception("Exception creating payment", extra={'payload': payload})
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
                payment = super(GocardlessPaymentManager, self).get_queryset().get(
                    id=event['links']['payment'])

                # save changes to object - this will also trigger internal handling
                payment.status = info.status
                payment.charge_date = info.charge_date
                payment.description = event['details']['description']
                payment.save()

            except GocardlessPayment.DoesNotExist:
                # odd...  log error
                # TODO: perhaps email admin to flag issue
                logger.exception("Payment object not found", extra={'event': event})

        except Exception:
            # odd - this should always be possible, perhaps there was a connection error
            logger.exception("Exception fetching payment info", extra={'event': event})

        return response


class GocardlessPayment(models.Model):
    id = models.TextField(unique=True, primary_key=True)
    created_at = models.DateTimeField(default=timezone.now)
    charge_date = models.DateField(default=timezone.now, blank=True)
    amount = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    currency = models.TextField()
    status = models.TextField()
    amount_refunded = models.IntegerField(default=0)
    reference = models.TextField(blank=True)
    payout_date = models.DateField(default=timezone.now, blank=True)
    creditor_id = models.TextField(blank=True)
    payout_id = models.TextField(blank=True)
    idempotency_key = models.TextField(blank=True)
    mandate = models.ForeignKey('GocardlessMandate', models.SET_NULL, blank=True, null=True)

    objects = GocardlessPaymentManager()

    class Meta:
        db_table = 'gocardlesspayment'
        app_label = 'main'

    def __str__(self):
        return '{} - {} - {}'.format(self.id, self.status, self.created_at.strftime('%Y-%m-%d'))

    def __init__(self, *args, **kwargs):
        super(GocardlessPayment, self).__init__(*args, **kwargs)
        self.old_status = self.status

    def save(self, force_insert=False, force_update=False, using=None):
        if self.status != self.old_status:
            # status has changed...  so need to act on it:
            if self.status == 'paid_out':
                # update date...  this is lazy, but probably good enough
                self.payout_date = timezone.now()

            # bubble status change event up to mandate
            if self.mandate is not None:
                self.mandate.handle_payment_updated(self)

        super(GocardlessPayment, self).save(force_insert, force_update, using)
        self.old_status = self.status
