from django.db import models
from django.utils import timezone

class Trademark(models.Model):
    number_to_show = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    applicant_name = models.CharField(max_length=100)
    published_url = models.URLField(blank=True)
    status = models.CharField(max_length=100)
    json = models.TextField()

    class Meta:
        ordering = ["number_to_show"]

    def __str__(self):
        return self.name
