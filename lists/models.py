from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
# from datetime import timedelta
from django.utils import timezone
import json
import shlex
import re
from json.decoder import JSONDecodeError
from decimal import Decimal

class List(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='lists_owned')
    agent = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='lists_agented')
    ju = models.ForeignKey('jus.Ju', blank=True, null=True)
    text = models.CharField(default='', max_length=140)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
        if self.ju:
            return sum(i.cost for i in self.item_set.filter(name__in = self.ju.items.keys()))
        else:
            return sum(i.cost for i in self.item_set.all())
        return None
    @property
    def items_to_text(self):
        return ';'.join(['{}:{:.2f}'.format(i.name,i.qty).upper() for i in self.item_set.all()])

    @property
    def qtys_by_ju(self):
        qtys=[]
        if self.ju.items:
            for k in sorted(self.ju.items.keys()):
                try:
                    qty = Item.objects.get(list=self, text__istartswith=k).qty
                except:
                    qty = '' 
                qtys.append(qty)
        return qtys

    def get_absolute_url(self):
        return reverse('view_list', args=[self.id])

    @staticmethod
    def create_new(first_item_text, owner=None, agent=None, ju=None):
        list_ = List(owner=owner, agent=agent, ju=ju)
        list_.full_clean()
        list_.save()
        item = Item(text=first_item_text, list=list_)
        item.save()
        return list_



class Item(models.Model):
        
    text = models.CharField(default='', max_length=140)
    list = models.ForeignKey(List, default=None)
    name = models.CharField(default='', max_length=140)
    qty =  models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    price =  models.DecimalField(blank=True, null=True, max_digits=15, decimal_places=2)
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
                last_n = Decimal(units[last_index])
            if last_index >= 2:
                prior_n = Decimal(units[last_index - 1])
        except Exception as e:
            print('----units:{},exception:{}'.format(units,e))
            pass
        if self.list.ju:
            if last_n != None:
                self.name = re.sub(r'\s+[-+]?[0-9]\d*(\.\d+)?\s*$','', self.text).upper()
                self.qty = last_n
            else:
                self.name = self.text.upper()
            try:
                self.price = self.list.ju.items[self.name]['price']
            except:
                self.price = 0
        elif last_n != None:
            if prior_n!=None:
                self.price = last_n
                self.qty = prior_n
                self.name = re.sub(r'\s+[-+]?[0-9]\d*(\.\d+)?\s+[-+]?[0-9]\d*(\.\d+)?\s*$','', self.text).upper()
            else:
                self.qty = last_n
                self.name = re.sub(r'\s+[-+]?[0-9]\d*(\.\d+)?\s*$','', self.text).upper()
        else:
            self.name = self.text.upper()

    @property
    def cost(self):
        if self.qty and self.price:
            return self.qty*self.price
        return 0


    class Meta:
        ordering = ('id',)
        unique_together = ('list', 'text')

    def __str__(self):
        return self.text
    pass

