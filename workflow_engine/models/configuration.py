from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import jsonfield


class Configuration(models.Model):
    '''Uses `generic relations <https://docs.djangoproject.com/en/2.2/ref/contrib/contenttypes/#generic-relations>`_
    to associate a databased JSON object with models that use the
    :class:`Configurable<workflow_engine.mixins.configurable.Configurable>` mixin.
    
    Examples are available in the Blue Sky Workflow Engine
    :ref:`configurations` documentation.
    '''

    content_type = models.ForeignKey(
        ContentType,
        default=None,
        null=True,
        on_delete=models.CASCADE
    )
    '''Generic relation type'''

    object_id = models.PositiveIntegerField(
        null=True
    )
    '''Generic relation id'''

    content_object = GenericForeignKey(
        'content_type',
        'object_id'
    )
    '''Combined generic relation type and id'''

    name = models.CharField(
        max_length=255,
        unique=True,
        null=True
    )
    '''Human readable'''

    configuration_type = models.CharField(
        max_length=255,
        default="unspecified",
        null=True
    )
    '''A well-known string to query'''

    json_object = jsonfield.JSONField(
        default={}
    )
    '''The data to be stored'''

    created_at = models.DateTimeField(
        auto_now_add=True,
        blank=True
    )
    '''Timestamp info, automatically set'''

    updated_at = models.DateTimeField(
        auto_now=True,
        blank=True
    )
    '''Timestamp info, automatically set'''

    def __str__(self):
        return str(self.name)
    '''Use human readable name'''
