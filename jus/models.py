from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
# from datetime import timedelta
from django.utils import timezone
import json
import shlex
import re
from json.decoder import JSONDecodeError
from lists.models import Item  as ListItem

class Product(models.Model):
   
    name = models.CharField(default='', max_length=300)
    desc = models.TextField(default='')
    href = models.TextField(default='')
    status = models.CharField(default='', max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class Ju(models.Model):
    def __init__(self, *args, **kwargs):
        super(Ju, self).__init__(*args, **kwargs)
        self.items_ = None
        self.sorted_items_ = None

    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    content = models.TextField(default='')
    address = models.CharField(default='', max_length=300)
    status = models.CharField(default='', max_length=30)
    stop_date_time = models.DateTimeField(blank=True, null=True)
    stop_date = models.CharField(default='', max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def parse_content(self):
        try:
            j = json.loads(self.content)
            self.address = j['address']
            self.stop_date = j['stop_date']
            self.status = j['status']
            self.items_ = j['items']
            self.sorted_items_ = sorted(self.items_.items())
            for k, v in self.sorted_items_:
                qty_sum = sum(
                    i.qty for i in ListItem.objects.filter(
                        list__ju=self, 
                        text__istartswith=k
                ))
                self.items_[k].update({'qty_sum': qty_sum})
                self.sorted_items_ = sorted(self.items_.items())
        except (JSONDecodeError, ValueError, KeyError) as e:
            print('------Exception:{}'.format(e))
            return False
        return True
    @property
    def name(self):
        return '{}:{}'.format(self.address, self.stop_date)
    @property
    def is_active(self):
        if self.status == 'active':
            return True
        return False
    @property
    def items(self):
        if not self.items_:
            self.parse_content()
        return self.items_

    @property
    def sorted_items(self):
        if not self.sorted_items_:
            self.parse_content()
        return self.sorted_items_

    @classmethod
    def active_ju(cls):
        return cls.objects.filter(status='active').first()

    def get_absolute_url(self):
        return reverse('view_ju', args=[self.id])

    class Meta:
        ordering = ('-updated_at', )

class Item(models.Model):
    
    key = models.CharField(default='', max_length=30)
    ju = models.ForeignKey(Ju, blank=True, null=True)
    product = models.ForeignKey(Product, blank=True, null=True)
    price = models.FloatField(default=0.0)
    desc = models.TextField(default='')
    href = models.TextField(default='')
    unit = models.FloatField(blank=True, null=True )
    min_qty = models.FloatField(blank=True, null=True )
    max_qty = models.FloatField(blank=True, null=True )
    min_total_qty = models.FloatField(blank=True, null=True )
    max_total_qty = models.FloatField(blank=True, null=True )
    updated_at = models.DateTimeField(auto_now=True)

    def total_qty(self):
        return sum([i.qty for i in ListItem.objects.filter(list__ju=self.ju,name=self.key)])


