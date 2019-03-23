from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import jsonfield


class Configuration(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        default=None,
        null=True
    )
    object_id = models.PositiveIntegerField(
        null=True
    )
    content_object = GenericForeignKey(
        'content_type',
        'object_id'
    )
    name = models.CharField(
        max_length=255,
        unique=True,
        null=True
    )
    configuration_type = models.CharField(
        max_length=255,
        default="unspecified",
        null=True
    )
    json_object = jsonfield.JSONField(
        default={}
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        blank=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        blank=True
    )

    def __str__(self):
        return str(self.name)