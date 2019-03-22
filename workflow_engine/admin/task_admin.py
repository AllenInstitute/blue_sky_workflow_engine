from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe


class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'enqueued_task_object_link',
        'storage_link',
        'duration',
        'retry_count',
        'start_run_time',
        'end_run_time',
        'run_state',
        )
    search_fields = (
        'id',
        'enqueued_task_object_id',
    )
    read_only_fields = (
        'start_run_time',
        'end_run_time',
        )
    list_select_related = (
        'run_state',
        )
    list_filter = (
        'job__workflow_node__workflow',
        'job__workflow_node',
        'run_state',
        'archived',
        )

    def enqueued_task_object_link(self, task_object):
        enqueued_object = task_object.enqueued_task_object
        clz = enqueued_object._meta.db_table
        return mark_safe('<a href="{}">{}</a>'.format(
            reverse("admin:{}_change".format(clz),
                    args=(enqueued_object.id,)),
            str(enqueued_object)))

    enqueued_task_object_link.short_description = "Enqueued Object"

    def workflow_link(self, job_object):
        return mark_safe('<a href="{}">{}</a>'.format(
            reverse("admin:workflow_engine_workflow_change",
                    args=(job_object.workflow_node.workflow.pk,)),
            str(job_object.workflow_node.workflow)))

    workflow_link.short_description = "Workflow"

    def storage_link(self, task_object):
        try:
            sd = task_object.job.get_strategy(
                ).get_task_storage_directory(task_object)
        except:
            sd = "-"

        return sd

    storage_link.short_description = 'Storage directory'


    def workflow_node_link(self, job_object):
        return mark_safe('<a href="{}">{}</a>'.format(
            reverse("admin:workflow_engine_workflownode_change",
                    args=(job_object.workflow_node.pk,)),
            str(job_object.workflow_node)))

    workflow_node_link.short_description = "Workflow Node"
