# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-28 22:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_user_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='car_no',
            field=models.CharField(blank=True, default='', max_length=40, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='car_seats_left',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='telephone',
            field=models.CharField(blank=True, default='', max_length=40, null=True),
        ),
    ]
