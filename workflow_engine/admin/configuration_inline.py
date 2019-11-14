from django.contrib.contenttypes.admin import GenericStackedInline
from workflow_engine.models import Configuration


class ConfigurationInline(GenericStackedInline):
    model = Configuration
    fields = (
        'name', 'configuration_type', 'json_object'
    )
    extra = 0
