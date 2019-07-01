from django.db import models
from django.utils import timezone
import logging

from .space_membership import SpaceMembership

# get instance of a logger
logger = logging.getLogger(__name__)


class SpaceManager(models.Manager):
    def active_spaces(self):
        return super(SpaceManager, self).get_queryset().filter(status="Active") | \
            super(SpaceManager, self).get_queryset().filter(status="Starting")

    def inactive_spaces(self):
        return super(SpaceManager, self).get_queryset().filter(status="Defunct") | \
            super(SpaceManager, self).get_queryset().filter(status="Suspended")

    def as_json(self):
        return {'spaces': list(
            super(SpaceManager, self).get_queryset().values('name', 'lat', 'lng',
                                                            'main_website_url', 'logo_image_url', 'status')
        )}

    def as_geojson(self):
        results = self.all()
        geo = {
            "type": "FeatureCollection",
            "features": []
        }
        for space in results:
            if space.valid_location():
                geo['features'].append(space.as_geojson_feature())
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
        ("Guernsey", "Guernsey"),
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

    # get membership type, returns: None, Supporter, Representative
    def member_type(self):
        if self.membership_status() != 'None':
            return 'Member'
        else:
            return 'None'
        # TODO: implement Representative stuff

    # get membership status, will return a APPROVAL_STATUS_CHOICES value
    def membership_status(self):
        return SpaceMembership.objects.get_membership_status(self)

    # get latest membership record for this user
    def current_membership(self):
        return SpaceMembership.objects.get_membership(self)

    # get all membership records for this user
    def memberships(self):
        return SpaceMembership.objects.get_memberships(self)
