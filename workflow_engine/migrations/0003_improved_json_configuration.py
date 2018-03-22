# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-03-16 07:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('workflow_engine', '0002_configuration'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuration',
            name='configuration_type',
            field=models.CharField(default='unspecified', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='configuration',
            name='content_type',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='configuration',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='configuration',
            name='name',
            field=models.CharField(max_length=255, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='configuration',
            name='object_id',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='configuration',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='configuration',
            name='json_object',
            field=jsonfield.fields.JSONField(default={}),
        ),
    ]