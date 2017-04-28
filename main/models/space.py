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
from .user import User

# get instance of a logger
logger = logging.getLogger(__name__)


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
        db_table = 'space'
        app_label = 'main'

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
