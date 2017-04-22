from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import uuid

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

    class Meta:
        # set default ordering to be on first_name
        ordering = ["first_name"]



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

    class Meta:
        ordering = ["name"]

    def publish(self):
        self.changed_date = timezone.now()
        self.save()

    def __str__(self):
        return self.name
