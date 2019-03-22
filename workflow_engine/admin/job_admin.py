from django.contrib import admin
from workflow_engine.workflow_controller import WorkflowController
from workflow_engine.models import (
    Task,
    RunState
)
from django.urls import reverse
from django.utils.safestring import mark_safe


def kill_jobs(modeladmin, request, queryset):
    kill_jobs.short_description = \
        "Kill jobs"

    for job in queryset:
        job.kill()


def set_killed(modeladmin, request, queryset):
    set_killed.short_description = \
        "Set job state to killed"

    for job in queryset:
        job.run_state = RunState.objects.get(name='PROCESS_KILLED')
        job.save()


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


def raise_priority(modeladmin, request, queryset):
    raise_priority.short_description = "Run sooner"

    for job_item in queryset:
        job_item.priority = job_item.priority - 10
        job_item.save()


def lower_priority(modeladmin, request, queryset):
    lower_priority.short_description = "Run later"

    for job_item in queryset:
        job_item.priority = job_item.priority + 10
        job_item.save()


def reset_priority(modeladmin, request, queryset):
    reset_priority.short_description = "Reset priority"

    for job_item in queryset:
        job_item.priority = job_item.workflow_node.priority
        job_item.save()


class TaskInline(admin.StackedInline):
    model = Task
    extra = 0


class JobAdmin(admin.ModelAdmin):
    search_fields = (
        'id',
        'enqueued_object_id',
    )
    list_display = (
        'id',
        'enqueued_object_link',
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
    actions = (
        kill_jobs,
        set_killed,
        start_jobs,
        enqueue_next,
        raise_priority,
        lower_priority,
        reset_priority)
    inlines = (TaskInline,)

    def enqueued_object_state(self, job_object):
        try:
            enqueued_object = job_object.get_enqueued_object()
            object_state = enqueued_object.object_state
            return object_state
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

    def enqueued_object_link(self, job_object):
        enqueued_object = job_object.enqueued_object
        clz = enqueued_object._meta.db_table
        return mark_safe('<a href="{}">{}</a>'.format(
            reverse("admin:{}_change".format(clz),
                    args=(enqueued_object.id,)),
            str(enqueued_object)))

    enqueued_object_link.short_description = "Enqueued Object"
