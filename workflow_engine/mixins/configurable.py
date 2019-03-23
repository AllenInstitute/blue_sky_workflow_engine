from django.db import models
from django.contrib.contenttypes.fields import GenericRelation

class Configurable(models.Model):
    configurations = GenericRelation('workflow_engine.Configuration')

    class Meta:
        abstract =True