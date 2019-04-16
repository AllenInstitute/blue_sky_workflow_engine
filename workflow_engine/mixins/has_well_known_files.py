from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

class HasWellKnownFiles(models.Model):
    well_known_files = GenericRelation(
        'workflow_engine.WellKnownFile',
        content_type_field='attachable_type',
        object_id_field='attachable_id'
    )

    class Meta:
        abstract = True
