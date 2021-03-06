# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-24 20:19
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0028_auto_20170424_1438'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupporterMembership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('Blank', 'Blank'), ('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], default='Blank', max_length=8)),
                ('fee', models.DecimalField(decimal_places=2, default=10.0, max_digits=8)),
                ('statement', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('started_at', models.DateTimeField(blank=True)),
                ('expired_at', models.DateTimeField(blank=True)),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.RemoveField(
            model_name='gocardlessmandate',
            name='space',
        ),
        migrations.RemoveField(
            model_name='gocardlessmandate',
            name='user',
        ),
        migrations.RemoveField(
            model_name='user',
            name='gocardless_customer_id',
        ),
        migrations.RemoveField(
            model_name='user',
            name='gocardless_mandate_id',
        ),
        migrations.RemoveField(
            model_name='user',
            name='gocardless_redirect_flow_id',
        ),
        migrations.RemoveField(
            model_name='user',
            name='gocardless_session_token',
        ),
        migrations.RemoveField(
            model_name='user',
            name='member_fee',
        ),
        migrations.RemoveField(
            model_name='user',
            name='member_statement',
        ),
        migrations.RemoveField(
            model_name='user',
            name='member_status',
        ),
        migrations.RemoveField(
            model_name='user',
            name='member_type',
        ),
        migrations.AddField(
            model_name='gocardlessmandate',
            name='redirect_flow_id',
            field=models.CharField(blank=True, max_length=33),
        ),
        migrations.AddField(
            model_name='gocardlessmandate',
            name='session_token',
            field=models.CharField(default='', max_length=33),
        ),
        migrations.AddField(
            model_name='supportermembership',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='gocardlessmandate',
            name='supporter_membership',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='main.SupporterMembership'),
        ),
    ]
