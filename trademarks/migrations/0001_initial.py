# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-14 10:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Trademark',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number_to_show', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=100)),
                ('applicant_name', models.CharField(max_length=100)),
                ('published_url', models.URLField(blank=True)),
                ('status', models.CharField(max_length=100)),
                ('json', models.TextField()),
            ],
            options={
                'ordering': ['number_to_show'],
            },
        ),
    ]