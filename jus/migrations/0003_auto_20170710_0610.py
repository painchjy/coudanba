# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-09 22:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jus', '0002_auto_20170709_2233'),
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(default='', max_length=30)),
                ('price', models.FloatField(default=0.0)),
                ('desc', models.TextField(default='')),
                ('href', models.TextField(default='')),
                ('unit', models.FloatField(blank=True, null=True)),
                ('min_qty', models.FloatField(blank=True, null=True)),
                ('max_qty', models.FloatField(blank=True, null=True)),
                ('min_total_qty', models.FloatField(blank=True, null=True)),
                ('max_total_qty', models.FloatField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ju', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='jus.Ju')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=300)),
                ('desc', models.TextField(default='')),
                ('href', models.TextField(default='')),
                ('status', models.CharField(default='', max_length=30)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='item',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='jus.Product'),
        ),
    ]
