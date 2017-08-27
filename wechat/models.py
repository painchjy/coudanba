from django.db import models
from django.conf import settings

class Requirement(models.Model):
    email = models.EmailField()
    content = models.TextField(default='')

class Location(models.Model):
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    msgid = models.TextField(default='')
    label = models.TextField(default='')
    latitude = models.FloatField(null=False, blank=False)
    longitude = models.FloatField(null=False, blank=False)
    precision = models.FloatField(default=0, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

class LocationHis(models.Model):
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    msgid = models.TextField(default='')
    label = models.TextField(default='')
    latitude = models.FloatField(null=False, blank=False)
    longitude = models.FloatField(null=False, blank=False)
    precision = models.FloatField(default=0, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
