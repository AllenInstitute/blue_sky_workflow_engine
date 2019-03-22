from django.contrib.contenttypes.fields import GenericRelation

class Configurable(object):
    configurations = GenericRelation(
        'workflow_engine.Configuration'
    )
