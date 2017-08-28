from django.contrib import auth
from django.db import models
# from jus.models import Ju,Location, LocationDepart, LocationUser
from django.apps import apps
import uuid

auth.signals.user_logged_in.disconnect(auth.models.update_last_login)

class User(models.Model):
    email = models.EmailField(primary_key=True)
    depart_name = models.TextField(default='N/A')
    display_name = models.TextField(default='' )
    group_name = models.TextField(default='' )
    avatar = models.TextField(default='' )
    car_no = models.CharField(default='' ,max_length=40, null=True, blank=True)
    car_seats_left = models.FloatField(default=0 )
    telephone = models.CharField(default='' ,max_length=40, null=True, blank=True)
    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'
    is_anonymous = False
    is_authenticated = True

    def is_admin(self):
        if self.email in ['13916341082@qq.com','zhang_jianhua@bankcomm.com','yeyt@bankcomm.com']:
            return True
        return False
    def prefered_locations(self):
        Location = apps.get_model('jus','Location')
        LocationDepart = apps.get_model('jus','LocationDepart')
        LocationUser = apps.get_model('jus','LocationUser')
        return Location.objects.filter(
            id__in=LocationDepart.objects.filter(
            depart_name=self.depart_name
        ).values_list('location').union(
            LocationUser.objects.filter(user=self).values_list('location')
        ))
        
    def closed_jus(self, ju_type=None):
        Ju = apps.get_model('jus','Ju')
        if ju_type:
            return Ju.objects.filter(
                id__in=self.lists_owned.all().values_list('ju'),
                ju_type=ju_type,
                status='close'
            )
        return Ju.objects.filter(
            id__in=self.lists_owned.all().values_list('ju'),
            status='close'
        )
    def active_jus(self, ju_type=None):
        Ju = apps.get_model('jus','Ju')
        if ju_type:
            return Ju.active_jus(ju_type=ju_type, locations=self.prefered_locations())
        return Ju.active_jus(locations=self.prefered_locations())
    def active_categories(self):
        return self.active_jus(ju_type='category')

    def created_categories(self):
        return self.ju_set.filter(ju_type='category')

    def created_jus(self):
        return self.ju_set.exclude(ju_type='category')

    def active_ju(self, ju_type=None):
        Ju = apps.get_model('jus','Ju')
        if ju_type:
            return Ju.active_ju(ju_type=ju_type, locations=self.prefered_locations())
        return Ju.active_ju(locations=self.prefered_locations())

    def next_ju(self,ju, ju_type=None):
        if ju_type:
            return ju.next(ju_type=ju_type, locations=self.prefered_locations())
        return ju.next(locations=self.prefered_locations())

class Token(models.Model):
    email = models.EmailField()
    uid = models.CharField(default=uuid.uuid4, max_length=40)

