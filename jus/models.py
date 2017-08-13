from django.db import models
from django.db.models import Q
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
from django.apps import apps
STATUS_CHOICES = (
    ('testing','测试'),
    ('active','开始'),
    ('ordering','待发货'),
    ('delivering','发货中'),
    ('paying','收款中'),
    ('close','关闭'),
)
JU_TYPE_CHOICES = (
    ('category','产品目录'),
    ('order','凑单'),
    ('didi','拼车'),
    ('plan','预算'),
    ('vote','投票'),
)

class Location(models.Model):
    name = models.CharField(default='', max_length=300)
    def get_absolute_url(self):
        return reverse('view_location', args=[self.id])
    def active_jus_counts(self):
        return self.ju_set.exclude(status__in=['close','testing']).count()
    def jus_counts(self):
        return self.ju_set.count()
    def lists_counts(self):
        return sum([ju.list_set.count() for ju in self.ju_set.all()])
    def user_counts(self):
        lu_counts = self.locationuser_set.exclude(
            user__depart_name=self.locationdepart_set.all().values('depart_name')
        ).count()
        User = apps.get_model('accounts', 'User')
        ld_user_counts = User.objects.filter(
            depart_name__in=LocationDepart.objects.filter(location=self).values('depart_name')
        ).count()
        return lu_counts + ld_user_counts
    def active_user_counts(self):
        lu_counts = self.locationuser_set.exclude(
            user__depart_name=self.locationdepart_set.all().values('depart_name')
        ).count()
        User = apps.get_model('accounts', 'User')
        Token = apps.get_model('accounts', 'Token')
        ld_user_counts = User.objects.filter(
            depart_name__in=LocationDepart.objects.filter(location=self).values('depart_name')
        ).filter(email__in=Token.objects.values('email').distinct()).count()
        return lu_counts + ld_user_counts

class LocationDepart(models.Model):
    location = models.ForeignKey(Location, blank=True, null=True)
    depart_name = models.CharField(default='', max_length=300)
class LocationUser(models.Model):
    location = models.ForeignKey(Location, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
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

    parent = models.ForeignKey('self',related_name='sub_jus', blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    location = models.ForeignKey(Location, blank=True, null=True)
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
                price  = v.get('price',0)
                if item.price != price:
                    item.price = price
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
        return d.get(self.status,'')
    def ju_type_name(self):
        d = dict(JU_TYPE_CHOICES)
        return d.get(self.ju_type,'')
    def family_members(self):
        if self.parent:
            return self.parent.family_members()
        members = [m for m in self.sub_jus.all()]
        # members = self.sub_jus.all()
        if members:
            members.append(self)
        else:
            members = [self]
        return members

    @property
    def sorted_items(self):
        i_ = self.items
        self.sorted_items_ = sorted(self.items.items())

        try:
            for k, v in self.items.items():
                qty_sum = sum(
                    i.qty for i in ListItem.objects.filter(
                        list__ju=self, 
                        text__istartswith=k
                ))
                qty_family_sum = sum(
                    i.qty for i in ListItem.objects.filter(
                        list__ju__in=self.family_members(), 
                        text__istartswith=k
                ))
                i_[k].update({'qty_sum': qty_sum, 'qty_family_sum': qty_family_sum})
                self.sorted_items_ = sorted(i_.items())
        except Exception as e:
            print('----exception:{}'.format(e))
            return  []
        return self.sorted_items_

    @classmethod
    def active_ju(cls, ju_type=None, locations=[]):
        if ju_type:
            return cls.objects.filter(
                    ~Q(status__in=['testing','close']),
                    Q(location__isnull=True)|Q(location__in=locations),
                    Q(ju_type=ju_type),
            ).first()
        return cls.objects.filter(
                ~Q(status__in=['testing','close']),
                ~Q(ju_type='category'),
                Q(location__isnull=True)|Q(location__in=locations),
        ).first()
    
    @classmethod
    def active_jus(cls, ju_type=None, locations=[]):
        if ju_type:
            return cls.objects.filter(
                    ~Q(status__in=['testing','close']),
                    Q(location__isnull=True)|Q(location__in=locations),
                    Q(ju_type=ju_type),
            )
        return cls.objects.filter(
                ~Q(status__in=['testing','close']),
                ~Q(ju_type='category'),
                Q(location__isnull=True)|Q(location__in=locations),
        )

    def next(self, ju_type=None,locations=[]):
        if ju_type:
            return Ju.objects.filter(
                ~Q(status__in=['testing','close']),
                ~Q(id=self.id),
                Q(location__isnull=True)|Q(location__in=locations),
                Q(updated_at__lt=self.updated_at),
                Q(ju_type=ju_type),
            ).first()
        return Ju.objects.filter(
            ~Q(status__in=['testing','close']),
            ~Q(ju_type='category'),
            ~Q(id=self.id),
            Q(location__isnull=True)|Q(location__in=locations),
            Q(updated_at__lt=self.updated_at),
        ).first()

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
    def total_qty_with_sub(self):
        jus = self.ju.sub_jus_set.all()
        jus.append(self.ju)
        return sum([i.qty for i in ListItem.objects.filter(list__ju__in=jus,name=self.key)])


