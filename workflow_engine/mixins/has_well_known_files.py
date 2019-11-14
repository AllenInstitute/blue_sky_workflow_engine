from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

class HasWellKnownFiles(models.Model):
    ''' An object using this mixin may optionally be associated
    with one or more :term:`well known file` on the file system.
    '''

    well_known_files = GenericRelation(
        'workflow_engine.WellKnownFile',
        content_type_field='attachable_type',
        object_id_field='attachable_id'
    )
    '''The generic association is automatically provided to models using this mixin
    '''

    class Meta:
        abstract = True
