from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
# from datetime import timedelta
from django.utils import timezone
import json
import shlex

class Ju(models.Model):
    content = models.TextField(default='')

    @property
    def name(self):
        j = json.loads(self.content)
        return j['address']+j['stop_date']

    @property
    def address(self):
        return json.loads(self.content)['address']

    @property
    def stop_date(self):
        return json.loads(self.content)['stop_date']

    @property
    def status(self):
        return json.loads(self.content)['status']

    @property
    def items(self):
        return json.loads(self.content)['items']

    @property
    def sorted_items(self):
        return sorted(json.loads(self.content)['items'].items())

    @classmethod
    def active_ju(cls):
        ju = cls.objects.first()
        if ju and ju.status == 'active':
            return ju

    class Meta:
        ordering = ('-id', )

class List(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    ju = models.ForeignKey(Ju, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def name(self):
        if self.ju:
            return "{:%Y-%m-%d %H:%M}${}${}".format(
                timezone.localtime(self.created_at), 
                self.ju.address,
                self.ju.stop_date
            )
        return "{:%Y-%m-%d %H:%M}${}".format(
            timezone.localtime(self.created_at), 
            #self.created_at + timedelta(hours=8), 
            self.item_set.first().text
        )
    @property
    def total_cost(self):
        return sum(i.cost for i in self.item_set.all())

    def get_absolute_url(self):
        return reverse('view_list', args=[self.id])

    @staticmethod
    def create_new(first_item_text, owner=None, ju=None):
        list_ = List(owner=owner, ju=ju)
        list_.full_clean()
        list_.save()
        Item.objects.create(text=first_item_text, list=list_)
        return list_



class Item(models.Model):
    def __init__(self, *args, **kwargs):
        super(Item, self).__init__(*args, **kwargs)
        self.name_ = None
        self.qty_ = None
        self.price_ = None
        
    text = models.TextField(default='')
    list = models.ForeignKey(List, default=None)
    
    def parse_text(self):
        units = shlex.split(self.text)
        try:
            self.name_ = units[0]
            self.qty_ = 0
            self.price_ = 0
            self.qty_ = float(units[1])
            self.price_ = float(units[2])
        except (ValueError,IndexError) as e:
            pass
        if self.list.ju:
            self.price_ = ju.items[self.name]['price']

    @property
    def name(self):
        if self.name_:
            return self.name_
        self.parse_text()
        return self.name_
    @property
    def qty(self):
        if self.qty_:
            return self.qty_
        self.parse_text()
        return self.qty_
    @property
    def price(self):
        if self.price_:
            return self.price_
        self.parse_text()
        return self.price_
    @property
    def cost(self):
        return self.qty*self.price
    class Meta:
        ordering = ('id',)
        unique_together = ('list', 'text')

    def __str__(self):
        return self.text
    pass

