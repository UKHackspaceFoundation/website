from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):

    SPACE_STATUS_CHOICES = (
        ("Blank", "Blank"),   #space is blank
        ("Pending", "Pending"),  # space relationship has changed, approval is pending
        ("Approved", "Approved"),  # space relationship has been approved
        ("Rejected", "Rejected"),  # space relationship has been rejected
    )

    # disable default username field
    username = None
    # add email, make it the unique field
    email = models.EmailField(_('email address'), unique=True)
    # relationship to users selected space
    space = models.ForeignKey('Space', models.SET_NULL, blank=True, null=True)
    # status of space relationship:
    space_status = models.CharField(max_length=8, choices=SPACE_STATUS_CHOICES, default='Blank')
    # who has been emailed to approve the space relationship:
    space_approver = models.EmailField(_('space approver email address'), blank=True)
    # when was the space approval requested (so we can flag slow responses):
    space_request_date = models.DateTimeField(default=timezone.now)
    # random hash to verify source of approve/reject responses
    space_request_key = models.CharField(max_length=32, blank=True)
    # override default
    USERNAME_FIELD = 'email'
    # disable default required fields
    REQUIRED_FIELDS = []

    class Meta:
        # set default ordering to be on first_name
        ordering = ["first_name"]



class SpaceManager(models.Manager):
    def active_spaces(self):
        return super(SpaceManager, self).get_queryset().filter(status="Active") | super(SpaceManager, self).get_queryset().filter(status="Starting")

    def inactive_spaces(self):
        return super(SpaceManager, self).get_queryset().filter(status="Defunct") | super(SpaceManager, self).get_queryset().filter(status="Suspended")

    def json_values(self):
        return super(SpaceManager, self).get_queryset().values('name', 'lat', 'lng', 'main_website_url', 'logo_image_url', 'status')

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
