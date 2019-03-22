from django.contrib.contenttypes.fields import GenericRelation

class HasWellKnownFiles(object):
    well_known_files = GenericRelation(
        'workflow_engine.WellKnownFile'
    )
