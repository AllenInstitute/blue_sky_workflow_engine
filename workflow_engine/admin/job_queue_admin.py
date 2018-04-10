from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe


class JobQueueAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'description',
        'job_strategy_class',
        'enqueued_object_class',
        'executable_link',
        'created_at',
        'updated_at',
        ]
    read_only_fields = (
        'executable_link',
        )
    list_select_related = (
        'executable',
        )
    list_filter = []
    actions = []
    inlines = []


    def executable_link(self, job_queue_object):
        return mark_safe('<a href="{}">{}</a>'.format(
            reverse("admin:workflow_engine_executable_change",
                    args=(job_queue_object.executable.pk,)),
            str(job_queue_object.executable)))

    executable_link.short_description = "Executable"


    def workflow_link(self, job_object):
        return mark_safe('<a href="{}">{}</a>'.format(
            reverse("admin:workflow_engine_workflow_change",
                    args=(job_object.workflow_node.workflow.pk,)),
            str(job_object.workflow_node.workflow)))

    workflow_link.short_description = "Workflow"
