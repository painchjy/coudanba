from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
# from datetime import timedelta
from django.utils import timezone
import json
import shlex
import re
from json.decoder import JSONDecodeError

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
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='lists_ju_owner')
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

class List(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    ju = models.ForeignKey('jus.Ju', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def name(self):
        if self.ju:
            return "{:%Y-%m-%d %H:%M}@{}~{}（{}）".format(
                timezone.localtime(self.created_at), 
                self.ju.address,
                self.ju.stop_date,
                self.ju.status
            )
        return "{:%Y-%m-%d %H:%M}@{}".format(
            timezone.localtime(self.created_at), 
            #self.created_at + timedelta(hours=8), 
            self.item_set.first().text
        )
    @property
    def total_cost(self):
        return sum(i.cost for i in self.item_set.all())
    @property
    def items_to_text(self):
        return ';'.join(['{}:{:.2f}'.format(i.name,i.qty).upper() for i in self.item_set.all()])

    @property
    def qtys_by_ju(self):
        qtys=[]
        for k,v in self.ju.sorted_items:
            try:
                qty = Item.objects.get(list=self, text__istartswith=k).qty
            except:
                qty = '' 
            qtys.append(qty)
        return qtys

    def get_absolute_url(self):
        return reverse('view_list', args=[self.id])

    @staticmethod
    def create_new(first_item_text, owner=None, ju=None):
        list_ = List(owner=owner, ju=ju)
        list_.full_clean()
        list_.save()
        item = Item(text=first_item_text, list=list_)
        item.save()
        return list_



class Item(models.Model):
        
    text = models.CharField(default='', max_length=140)
    list = models.ForeignKey(List, default=None)
    name = models.CharField(default='', max_length=140)
    qty =  models.FloatField(default=0.0)
    price =  models.FloatField(default=0.0)
    def save(self):
        self.parse_text()
        super(Item, self).save()

    def parse_text(self):
        units = shlex.split(self.text)
        last_index = len(units) - 1
        last_n = None
        prior_n = None
        try:
            if last_index >= 1:
                last_n = float(units[last_index])
            if last_index >= 2:
                prior_n = float(units[last_index - 1])
        except (ValueError,IndexError) as e:
            pass
        if self.list.ju:
            if last_n != None:
                self.name = re.sub(r'\s+[-+]?[0-9]\d*(\.\d+)?\s*$','', self.text)
                self.qty = last_n
            else:
                self.name = self.text
            self.price = self.list.ju.items[self.name.upper()]['price']
        elif last_n != None:
            if prior_n!=None:
                self.price = last_n
                self.qty = prior_n
                self.name = re.sub(r'\s+[-+]?[0-9]\d*(\.\d+)?\s+[-+]?[0-9]\d*(\.\d+)?\s*$','', self.text)
            else:
                self.qty = last_n
                self.name = re.sub(r'\s+[-+]?[0-9]\d*(\.\d+)?\s*$','', self.text)
        else:
            self.name = self.text

    @property
    def cost(self):
        return self.qty*self.price

    class Meta:
        ordering = ('id',)
        unique_together = ('list', 'text')

    def __str__(self):
        return self.text
    pass

