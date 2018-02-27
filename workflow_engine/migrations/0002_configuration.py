# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-02-23 21:26
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('workflow_engine', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Configuration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('json_object', jsonfield.fields.JSONField(default=dict)),
            ],
        ),
    ]
