from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
# from datetime import timedelta
from django.utils import timezone
import json
import shlex
import re
from jsonfield import JSONField
from json.decoder import JSONDecodeError
from lists.models import Item  as ListItem
STATUS_CHOICES = (
    ('testing','测试'),
    ('active','开始'),
    ('ordering','待发货'),
    ('delivering','发货中'),
    ('paying','收款中'),
    ('close','关闭'),
)
JU_TYPE_CHOICES = (
    ('order','凑单'),
    ('didi','拼车'),
    ('plan','预算'),
)

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
        self.sorted_items_ = None

    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    content = models.TextField(default='')
    items = JSONField()
    address = models.CharField(default='', max_length=300)
    status = models.CharField(default='', max_length=30,choices=STATUS_CHOICES)
    ju_type = models.CharField(default='', max_length=30,choices=JU_TYPE_CHOICES)
    stop_date_time = models.DateTimeField(blank=True, null=True)
    stop_date = models.CharField(default='', max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def db_triggers(self):
        for k, v in self.sorted_items:
            item = self.item_set.filter(key=k).first()
            if item:
                if item.price != v['price']:
                    item.price = v['price']
                    ListItem.objects.filter(list__ju=self, text__istartswith=k).update(price=item.price)
            else:
                item = Item(ju=self, key=k)

            item.__dict__.update(v)
            item.save()

    @property
    def name(self):
        return '{}:{}'.format(self.address, self.stop_date)
    @property
    def is_active(self):
        if self.status == 'active':
            return True
        return False
    def status_name(self):
        d = dict(STATUS_CHOICES)
        return d[self.status]

    @property
    def sorted_items(self):
        if self.sorted_items_:
            return self.sorted_items_
        i_ = dict(self.items.items())
        self.sorted_items_ = sorted(self.items.items())
        try:
            for k, v in self.sorted_items_:
                qty_sum = sum(
                    i.qty for i in ListItem.objects.filter(
                        list__ju=self, 
                        text__istartswith=k
                ))
                i_[k].update({'qty_sum': qty_sum})
                self.sorted_items_ = sorted(i_.items())
        except Exception as e:
            return  []
        return self.sorted_items_

    @classmethod
    def active_ju(cls):
        return cls.objects.exclude(status__in=['testing','close']).first()

    def get_absolute_url(self):
        return reverse('view_ju', args=[self.id])

    def can_order(self, user):
        if self.status == 'active':
            return True
        if self.status == 'testing' and user == self.owner:
            return True
        return False

    class Meta:
        ordering = ('-updated_at', )

class Item(models.Model):
    
    key = models.CharField(default='', max_length=30)
    ju = models.ForeignKey(Ju, blank=True, null=True)
    product = models.ForeignKey(Product, blank=True, null=True)
    price = models.DecimalField(default=0.0, max_digits=15, decimal_places=2)
    desc = models.TextField(default='')
    href = models.TextField(default='')
    unit = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    min_qty = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2 )
    max_qty = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2 )
    min_total_qty = models.DecimalField(blank=True, null=True, max_digits=15, decimal_places=2 )
    max_total_qty = models.DecimalField(blank=True, null=True, max_digits=15, decimal_places=2 )
    updated_at = models.DateTimeField(auto_now=True)

    def total_qty(self):
        return sum([i.qty for i in ListItem.objects.filter(list__ju=self.ju,name=self.key)])


