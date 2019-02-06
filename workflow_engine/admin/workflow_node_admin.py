from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline
from workflow_engine.models import Configuration
from django.urls import reverse
from django.utils.safestring import mark_safe


class ConfigurationInline(GenericStackedInline):
    model = Configuration
    fields = (
        'name', 'configuration_type', 'json_object'
    )
    extra = 0


class WorkflowNodeAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'job_queue',
        'parent',
        'workflow',
        'batch_size',
        'priority',
        'overwrite_previous_job',
        'max_retries',
        'is_head',
        'disabled',
        'archived'
        ]
    read_only_fields = (
        )
    list_select_related = (
        )
    list_filter = [
        'workflow',
        'is_head',
        'disabled',
        'archived']
    actions = []
    inlines = (ConfigurationInline,)
