from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
from workflow_engine.models import (
    Configuration,
    WorkflowNode
)


class ConfigurationInline(GenericStackedInline):
    model = Configuration
    fields = (
        'name', 'configuration_type', 'json_object'
    )
    extra = 0

class SourcesInline(admin.TabularInline):
    model = WorkflowNode.sources.through
    fk_name = 'source'
    extra = 0

class SinksInline(admin.TabularInline):
    model = WorkflowNode.sinks.through
    fk_name = 'sink'
    extra = 0


class WorkflowNodeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'job_queue',
        'workflow',
        'source_names',
        'sink_names',
        'batch_size',
        'priority',
        'overwrite_previous_job',
        'max_retries',
        'disabled',
        'archived'
    )
    read_only_fields = (
    )
    list_select_related = (
    )
    list_filter = (
        'workflow',
        'disabled',
        'archived'
    )
    filter_horizontal = (
        'sources',
        'sinks'
    )
    actions = ()
    inlines = (ConfigurationInline, SourcesInline, SinksInline)

    def source_names(self, node_obj):
        return ','.join(str(n) for n in node_obj.sources.all())

    def sink_names(self, node_obj):
        return ','.join(str(n) for n in node_obj.sinks.all())
