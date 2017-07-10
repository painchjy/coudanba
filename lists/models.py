from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
# from datetime import timedelta
from django.utils import timezone
import json
import shlex
import re
from json.decoder import JSONDecodeError

class List(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    ju = models.ForeignKey('jus.Ju', blank=True, null=True)
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
        return None
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
        return self.qty*self.price

    class Meta:
        ordering = ('id',)
        unique_together = ('list', 'text')

    def __str__(self):
        return self.text
    pass

