from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
# from datetime import timedelta
from django.utils import timezone
import json
import shlex
import re
from json.decoder import JSONDecodeError
from lists.models import Item 

class Ju(models.Model):
    def __init__(self, *args, **kwargs):
        super(Ju, self).__init__(*args, **kwargs)
        self.name_ = None
        self.address_ = None
        self.stop_date_ = None
        self.status_ = None
        self.items_ = None
        self.sorted_items_ = None

    
    content = models.TextField(default='')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    stop_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def parse_content(self):
        try:
            j = json.loads(self.content)
            self.name_ = j['address']+j['stop_date']
            self.address_ = j['address']
            self.stop_date_ = j['stop_date']
            self.status_ = j['status']
            self.items_ = j['items']
            self.sorted_items_ = sorted(self.items_.items())
            for k, v in self.sorted_items_:
                qty_sum = sum(
                    i.qty for i in Item.objects.filter(
                        list__ju=self, 
                        text__istartswith=k
                ))
                self.items_[k].update({'qty_sum': qty_sum})
            self.sorted_items_ = sorted(self.items_.items())
        except (JSONDecodeError, ValueError, KeyError):
            return False
        return True
    @property
    def name(self):
        if not self.name_:
            self.parse_content()
        return self.name_


    @property
    def address(self):
        if not self.address_:
            self.parse_content()
        return self.address_

    @property
    def stop_date(self):
        if not self.stop_date_:
            self.parse_content()
        return self.stop_date_

    @property
    def status(self):
        if not self.status_:
            self.parse_content()
        return self.status_

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
        ju = cls.objects.first()
        if ju and ju.status == 'active':
            return ju

    def get_absolute_url(self):
        return reverse('view_ju', args=[self.id])

    class Meta:
        ordering = ('-updated_at', )

