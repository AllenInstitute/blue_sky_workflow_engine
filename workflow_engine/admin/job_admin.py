from django.contrib import admin
from workflow_engine.workflow_controller import WorkflowController
from workflow_engine.models.task import Task
from django.urls import reverse
from django.utils.safestring import mark_safe


def kill_jobs(modeladmin, request, queryset):
    kill_jobs.short_description = \
        "Kill jobs"

    for job in queryset:
        job.kill()


def start_jobs(modeladmin, request, queryset):
    start_jobs.short_description = \
        "Start jobs"

    job_ids = [item.id for item in queryset]
    WorkflowController.set_jobs_for_run_by_id(job_ids)


def enqueue_next(modeladmin, request, queryset):
    enqueue_next.short_description = \
        "Enqueue next queue"

    for job_item in queryset:
        WorkflowController.enqueue_next_queue_by_job_id(job_item.id)


class TaskInline(admin.StackedInline):
    model = Task
    extra = 0


class JobAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'enqueued_object_id',
        'enqueued_object',
        'enqueued_object_state',
        'start_run_time',
        'duration',
        'workflow_link',
        'workflow_node_link',
        'run_state',
        'task_ids',
        'archived',
        )
    read_only_fields = (
        'workflow_link',
        'workflow_node_link',
        'enqueued_object_state'
        )
    list_select_related = (
        'workflow_node',
        'workflow_node__workflow',
        'run_state',
        )
    list_filter = (
        'workflow_node__workflow',
        'workflow_node',
        'run_state',
        'archived',
        )
    actions = (kill_jobs, start_jobs, enqueue_next)
    inlines = (TaskInline,)

    def enqueued_object_state(self, job_object):
        try:
            enqueued_object = job_object.get_enqueued_object()
            workflow_state = enqueued_object.workflow_state
            return workflow_state
        except:
            return "-"


    def workflow_link(self, job_object):
        return mark_safe('<a href="{}">{}</a>'.format(
            reverse("admin:workflow_engine_workflow_change",
                    args=(job_object.workflow_node.workflow.pk,)),
            str(job_object.workflow_node.workflow)))

    workflow_link.short_description = "Workflow"


    def workflow_node_link(self, job_object):
        return mark_safe('<a href="{}">{}</a>'.format(
            reverse("admin:workflow_engine_workflownode_change",
                    args=(job_object.workflow_node.pk,)),
            str(job_object.workflow_node)))

    workflow_node_link.short_description = "Workflow Node"
