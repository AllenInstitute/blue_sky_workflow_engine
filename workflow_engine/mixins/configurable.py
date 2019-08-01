from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

class Configurable(models.Model):
    ''' Provides a relation to associate configurable objects
    with one or more :term:`configuration` objects.

    The JSON configurations can be used when a database column or
    :term:`well known file` is not desired,
    or for when the data to be stored is naturally represented as JSON.
    '''

    configurations = GenericRelation('workflow_engine.Configuration')

    class Meta:
        abstract =True