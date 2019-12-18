from django.contrib import admin
from .configuration_inline import ConfigurationInline
from workflow_engine import signatures
from workflow_engine.models import WorkflowNode


def start_jobs(ModelAdmin, request, queryset):
    start_jobs.short_description = \
        'Start jobs in node'
    
    for node in queryset:
        signatures.run_workflow_node_jobs_signature.delay(node.id)


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
        #'source_names',
        #'sink_names',
        'batch_size',
        'priority',
        'overwrite_previous_job',
        'max_retries',
        'disabled',
        'archived'
    )
    search_fields = (
        'job_queue__name',
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
    actions = (
        start_jobs,
    )
    inlines = (ConfigurationInline, SourcesInline, SinksInline)

    def get_queryset(self, request):
        return self.model.all_objects.get_queryset()

    def source_names(self, node_obj):
        return ','.join(str(n) for n in node_obj.sources.all())

    def sink_names(self, node_obj):
        return ','.join(str(n) for n in node_obj.sinks.all())
