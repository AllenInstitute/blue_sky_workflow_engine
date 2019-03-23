from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

class HasWellKnownFiles(models.Model):
    well_known_files = GenericRelation(
        'workflow_engine.WellKnownFile'
    )

    class Meta:
        abstract = True
