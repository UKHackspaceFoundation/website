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
from .supporter_membership import SupporterMembership

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
        db_table = 'user'
        app_label = 'main'

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
