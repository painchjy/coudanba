# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-09 14:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jus', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ju',
            name='address',
            field=models.CharField(default='', max_length=300),
        ),
        migrations.AddField(
            model_name='ju',
            name='status',
            field=models.CharField(default='', max_length=30),
        ),
        migrations.AddField(
            model_name='ju',
            name='stop_date',
            field=models.CharField(default='', max_length=30),
        ),
    ]