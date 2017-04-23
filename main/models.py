from django.db import models
from django.utils import timezone
from django.contrib.auth.models import (AbstractUser,BaseUserManager)
from django.utils.translation import gettext_lazy as _
import uuid


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
        user.save(using=self._db)
        return user

class User(AbstractUser):

    APPROVAL_STATUS_CHOICES = (
        ("Blank", "Blank"),   #space is blank
        ("Pending", "Pending"),  # space relationship has changed, approval is pending
        ("Approved", "Approved"),  # space relationship has been approved
        ("Rejected", "Rejected"),  # space relationship has been rejected
    )

    MEMBER_TYPE_CHOICES = (
        ("None", "None"),  # i.e. a manager of profile info
        ("Supporter", "Supporter"),
        ("Representative", "Representative"),
    )

    # disable default username field
    username = None
    # add email, make it the unique field
    email = models.EmailField(_('email address'), unique=True)
    # override default
    USERNAME_FIELD = 'email'

    # whether user account is active (i.e. password has been reset after initial signup)
    active = models.BooleanField(default=False)

    # what type of member is this?
    member_type = models.CharField(max_length=14, choices=MEMBER_TYPE_CHOICES, default='None')
    # member application status
    member_status = models.CharField(max_length=8, choices=APPROVAL_STATUS_CHOICES, default='Blank')
    # member subscription fee (chosen by user)
    member_fee = models.DecimalField(max_digits=8, decimal_places=2, default=10.00)
    # application statement - aka: why i should be a member statement
    member_statement = models.TextField(blank=True)

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

    # gocardless redirect flow id
    gocardless_redirect_flow_id = models.CharField(max_length=33, blank=True)
    gocardless_session_token = models.CharField(max_length=33, default='')
    gocardless_mandate_id = models.CharField(max_length=16, blank=True)
    gocardless_customer_id = models.CharField(max_length=16, blank=True)

    # disable default required fields
    REQUIRED_FIELDS = []

    objects = SpaceUserManager();

    class Meta:
        # set default ordering to be on first_name
        ordering = ["first_name"]



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


class GocardlessPayment(models.Model):
    id = models.CharField(max_length=16, unique=True, primary_key=True)
    created_at = models.DateTimeField(default=timezone.now)
    charge_date = models.DateField(default=timezone.now)
    amount = models.IntegerField()
    description = models.CharField(max_length=100)
    currency = models.CharField(max_length=10)
    status = models.CharField(max_length=26)
    amount_refunded = models.IntegerField()
    reference = models.CharField(max_length=10)
    payout_date = models.DateField(default=timezone.now)
    mandate_id = models.CharField(max_length=16)
    creditor_id = models.CharField(max_length=16)
    payout_id = models.CharField(max_length=16)
