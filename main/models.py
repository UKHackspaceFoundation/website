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


class SpaceUserManager(BaseUserManager):
    def create_user(self, email, password=None, space=None):
        """
        Creates and saves a User with the given email, space
        and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            space=space,
        )

        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a superuser with the given email
        and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractUser):

    APPROVAL_STATUS_CHOICES = (
        ("Blank", "Blank"),   #space is blank
        ("Pending", "Pending"),  # space relationship has changed, approval is pending
        ("Approved", "Approved"),  # space relationship has been approved
        ("Rejected", "Rejected"),  # space relationship has been rejected
    )

    # disable default username field
    username = None
    # add email, make it the unique field
    email = models.EmailField(_('email address'), unique=True)
    # override default
    USERNAME_FIELD = 'email'

    # whether user account is active (i.e. password has been reset after initial signup)
    active = models.BooleanField(default=False)

    # relationship to users selected space
    space = models.ForeignKey('Space', models.SET_NULL, blank=True, null=True)
    # status of space relationship:
    space_status = models.CharField(max_length=8, choices=APPROVAL_STATUS_CHOICES, default='Blank')
    # who has been emailed to approve the space relationship:
    space_approver = models.EmailField(_('space approver email address'), blank=True)
    # when was the space approval requested (so we can flag slow responses):
    space_request_date = models.DateTimeField(default=timezone.now)
    # random hash to verify source of approve/reject responses
    space_request_key = models.CharField(max_length=32, blank=True)

    # disable default required fields
    REQUIRED_FIELDS = []

    objects = SpaceUserManager();

    class Meta:
        # set default ordering to be on first_name
        ordering = ["first_name"]

    def name(self):
        return self.first_name + ' ' + self.last_name

    # get membership type, returns: None, Supporter, Representative
    def member_type(self):
        if self.supporter_status() != 'None':
            return 'Supporter'
        else:
            return 'None'
        # TODO: implement Representative stuff

    # get supporter status, will return a APPROVAL_STATUS_CHOICES value
    def supporter_status(self):
        return SupporterMembership.objects.get_membership_status(self)

    # get latest membership record for this user
    def supporter_membership(self):
        return SupporterMembership.objects.get_membership(self)

    def sync_payments(self):
        # get gocardless client object
        client = gocardless_pro.Client(
            access_token = getattr(settings, "GOCARDLESS_ACCESS_TOKEN", None),
            environment = getattr(settings, "GOCARDLESS_ENVIRONMENT", None)
        )

        # fetch associated gocardless payments
        try:
            payments = client.payments.list(params={"customer": self.gocardless_customer_id}).records

            # TODO: sync payments with database

        except Exception as e:
            logger.error("Error in sync_payments - exception retrieving payments: " + repr(e), extra={'user':self})



class SpaceManager(models.Manager):
    def active_spaces(self):
        return super(SpaceManager, self).get_queryset().filter(status="Active") | super(SpaceManager, self).get_queryset().filter(status="Starting")

    def inactive_spaces(self):
        return super(SpaceManager, self).get_queryset().filter(status="Defunct") | super(SpaceManager, self).get_queryset().filter(status="Suspended")

    def as_json(self):
        return {'spaces': list(
            super(SpaceManager, self).get_queryset().values('name', 'lat', 'lng', 'main_website_url', 'logo_image_url', 'status')
        )}

    def as_geojson(self):
        results = self.all()
        geo = {
            "type": "FeatureCollection",
            "features": []
        }
        for space in results:
            if space.valid_location():
                geo['features'].append( space.as_geojson_feature() )
        return geo


class Space(models.Model):

    STATUS_CHOICES = (
        ("Active", "Active"),
        ("Starting", "Starting"),
        ("Suspended", "Suspended"),
        ("Defunct", "DEFUNCT"),
    )

    COUNTRY_CHOICES = (
        ("England", "England"),
        ("Guernsey","Guernsey"),
        ("Ireland", "Ireland"),
        ("Scotland", "Scotland"),
        ("Wales", "Wales"),
    )

    name = models.CharField(max_length=100)
    town = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=50, choices=COUNTRY_CHOICES, default='ENGLAND')
    region = models.CharField(max_length=100, blank=True)
    have_premises = models.BooleanField(default=False)
    address_first_line = models.CharField(max_length=250, blank=True)
    postcode = models.CharField(max_length=9, blank=True)
    lat = models.DecimalField('latitude', max_digits=10, decimal_places=7)
    lng = models.DecimalField('longitude', max_digits=10, decimal_places=7)
    main_website_url = models.URLField(blank=True)
    logo_image_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    changed_date = models.DateTimeField(default=timezone.now)
    email = models.CharField(max_length=200, blank=True)

    objects = SpaceManager()

    class Meta:
        ordering = ["name"]

    def publish(self):
        self.changed_date = timezone.now()
        self.save()

    def __str__(self):
        return self.name

    def valid_location(self):
        return (self.lng != 0 and self.lat != 0)

    def as_geojson_feature(self):
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(self.lng), float(self.lat)]
            },
            "properties": {
                "name": self.name,
                "url": self.main_website_url,
                "status": self.status,
                "logo": self.logo_image_url
            }
        }


class SupporterMembershipManager(models.Manager):
    # get all membership records for user
    def get_membership_history(self, user):
        return super(SupporterMembershipManager, self).get_queryset().filter(user=user)

    # get latest membership for user
    def get_membership(self, user):
        return self.get_membership_history(user).latest('created_at')

    # get latest membership status for user
    def get_membership_status(self, user):
        try:
            return self.get_membership(user).status
        except SupporterMembership.DoesNotExist as e:
            return 'None'


class SupporterMembership(models.Model):

    APPROVAL_STATUS_CHOICES = (
        ("Pending", "Pending"),  # approval is pending
        ("Approved", "Approved"),  # application has been approved
        ("Rejected", "Rejected"),  # application has been rejected
    )

    # application status
    status = models.CharField(max_length=8, choices=APPROVAL_STATUS_CHOICES, default='Pending')
    # how many times have we successfully sent an approval request email:
    approval_request_count = models.IntegerField(default=0)
    # subscription fee (chosen by user)
    fee = models.DecimalField(max_digits=8, decimal_places=2, default=10.00)
    # application statement - aka: why i should be a member statement
    statement = models.TextField(blank=True)
    # when was the application membership created
    created_at = models.DateTimeField(default=timezone.now)
    # when was the first payment received
    started_at = models.DateTimeField(null=True)
    # when did the membership expire
    expired_at = models.DateTimeField(null=True)
    # what user is this associated with:
    user = models.ForeignKey('User', models.CASCADE)
    # gocardless redirect flow id
    redirect_flow_id = models.CharField(max_length=33, blank=True)
    # session token (for redirect flow)
    session_token = models.CharField(max_length=33, default='')

    objects = SupporterMembershipManager()

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.user.name() + ' - ' + self.created_at.strftime('%Y-%m-%d')

    # is there an active mandate?
    def has_active_mandate(self):
        try:
            return self.mandate().status != ''
        except GocardlessMandate.DoesNotExist as e:
            return False

    # get mandate status or throw DoesNotExist
    def mandate_status(self):
        return self.mandate().status

    # get latest mandate record for this supporter membership
    def mandate(self):
        return GocardlessMandate.objects.get_mandate_for_supporter_membership(self)

    # create a new gocardless redirect flow and return redirect_url
    def get_redirect_flow_url(self, request):
        # get gocardless client object
        client = gocardless_pro.Client(
            access_token = getattr(settings, "GOCARDLESS_ACCESS_TOKEN", None),
            environment = getattr(settings, "GOCARDLESS_ENVIRONMENT", None)
        )

        # generate a new session_token
        self.session_token = uuid.uuid4().hex

        # create a redirect_flow, pre-fill the users name and email
        redirect_flow = client.redirect_flows.create(
            params={
                "description" : "Hackspace Foundation Individual Membership",
                "session_token" : self.session_token,
                "success_redirect_url" : request.build_absolute_uri( reverse('join_supporter_step3') ),
                "prefilled_customer": {
                    "given_name": self.user.first_name,
                    "family_name": self.user.last_name,
                    "email": self.user.email
                }
            }
        )

        self.redirect_flow_id = redirect_flow.id
        self.save()

        return redirect_flow.redirect_url

    # attempt to complete a redirect flow and return new mandate object
    # will throw Gocardless and/or other exceptions
    def complete_redirect_flow(self, request):
        # get gocardless client object
        client = gocardless_pro.Client(
            access_token = getattr(settings, "GOCARDLESS_ACCESS_TOKEN", None),
            environment = getattr(settings, "GOCARDLESS_ENVIRONMENT", None)
        )

        # try to complete the redirect flow
        redirect_flow = client.redirect_flows.complete(
            request.GET.get('redirect_flow_id', ''),
            params = {
                'session_token': self.session_token
            }
        )

        # fetch the detailed mandate info
        mandate_detail = client.mandates.get( redirect_flow.links.mandate )

        # create new mandate object
        mandate = GocardlessMandate(
            id = redirect_flow.links.mandate,
            supporter_membership = self,
            reference = mandate_detail.reference,
            status = mandate_detail.status,
            customer_id = mandate_detail.links.customer,
            creditor_id = mandate_detail.links.creditor,
            customer_bank_account_id = mandate_detail.links.customer_bank_account
        )
        mandate.save()

        return mandate

    # send approval request email
    def send_approval_request(self, request):
        # get template
        htmly = get_template('join_supporter/supporter_application_email.html')

        # build context
        d = Context({
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'note': self.statement,
            'fee': self.fee,
            'approve_url': request.build_absolute_uri(reverse('supporter-approval', kwargs={'session_token':self.session_token, 'action':'approve'} )),
            'reject_url': request.build_absolute_uri(reverse('supporter-approval', kwargs={'session_token':self.session_token, 'action':'reject'} ))
        })

        # prep headers
        subject = "Supporter Member Application from " + self.user.first_name +" " + self.user.last_name
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
        to = getattr(settings, "BOARD_EMAIL", None)

        # render template
        message = htmly.render(d)
        try:
            # send email
            msg = EmailMessage(subject, message, to=[to], from_email=from_email)
            msg.content_subtype = 'html'
            msg.send()

            # track how many times we've sent a request
            self.approval_request_count += 1;
            self.save()

        except Exception as e:
            # TODO: oh dear - how should we handle this gracefully?!?
            logger.error("Error in send_approval_request - failed to send email: "+str(e), extra={'SupporterMembership':self})





    # TODO: update started_at when first payment received
    # TODO: update expired_at when new payment received
    # TODO: get associated mandates


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

    # is_supporter_mandate
    def is_supporter_mandate(self):
        return self.supporter_membership is not None

    # TODO: is_space_mandate

    # is_active - is this mandate active
    def is_active(self):
        return not (self.status == 'failed' or self.status == 'expired' or self.status == 'cancelled')

    # TODO: get associated payments
    # TODO: get latest payment



class GocardlessPaymentManger(models.Manager):
    # get_or_create that populates fields from json
    # e.g. as received from gocardless webhook or payment creation api
    # payload should be a dict, e.g. parsed from webhook json
    def get_or_create_from_payload(self, payload):
        try:
            # create with required fields only
            obj, created = super(GocardlessPaymentManger, self).get_or_create(
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
            if hasattr(payload.links, 'mandate') and payload.links.mandate is not None:
                obj.mandate_id = payload.links.mandate
            if hasattr(payload.links, 'creditor') and payload.links.creditor is not None:
                obj.creditor_id = payload.links.creditor
            if hasattr(payload.links, 'payout') and payload.links.payout is not None:
                obj.payout_id = payload.links.payout

            obj.save()
            return obj

        except Exception as e:
            logger.error("Error in GocardlessPaymentManager.get_or_create_from_payload - exception creating payment: " + repr(e), extra={'payload':payload})
            return None


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
    user = models.ForeignKey('User', models.SET_NULL, blank=True, null=True)
    space = models.ForeignKey('Space', models.SET_NULL, blank=True, null=True)

    objects = GocardlessPaymentManger()
