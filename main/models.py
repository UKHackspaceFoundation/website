from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []



class Space(models.Model):
    name = models.CharField(max_length=100)
    longname = models.CharField(max_length=200)
    town = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=50)
    region = models.CharField(max_length=100)
    have_premises = models.BooleanField()
    town_not_in_name = models.BooleanField()
    address_first_line = models.CharField(max_length=250, blank=True)
    postcode = models.CharField(max_length=9, blank=True)
    lat = models.DecimalField('latitude', max_digits=10, decimal_places=7)
    lng = models.DecimalField('longitude', max_digits=10, decimal_places=7)
    main_website_url = models.URLField(blank=True)
    logo_image_url = models.URLField(blank=True)
    status = models.CharField(max_length=20)
    classification = models.CharField(max_length=20)
    changed_date = models.DateTimeField(default=timezone.now)

    def publish(self):
        self.changed_date = timezone.now()
        self.save()

    def __str__(self):
        return self.name
