from django.contrib import admin
from workflow_client import signatures
from workflow_engine.models import (
    Task,
)
from django.urls import reverse
from django.utils.safestring import mark_safe


def kill_jobs(modeladmin, request, queryset):
    kill_jobs.short_description = \
        "Kill jobs"

    for job in queryset:
        signatures.kill_job_signature.delay(job.id)


def set_killed(modeladmin, request, queryset):
    set_killed.short_description = \
        "Set job state to killed"

    for job in queryset:
        job.set_process_killed_state()


def start_jobs(modeladmin, request, queryset):
    start_jobs.short_description = "Start jobs"

    job_ids = [item.id for item in queryset]
    signatures.run_jobs_by_id_signature.delay(job_ids)


def enqueue_next(modeladmin, request, queryset):
    enqueue_next.short_description = "Enqueue next queue"

    for job_item in queryset:
        signatures.enqueue_next_queue_signature.delay(job_item.id)


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
        'running_state',
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
        )
    list_filter = (
        'workflow_node__workflow',
        'workflow_node',
        'running_state',
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

    def get_queryset(self, request):
        return self.model.all_objects.get_queryset()

    def enqueued_object_state(self, job_object):
        try:
            #enqueued_object = job_object.enqueued_object
            enqueued_object = job_object.enqueued_object_type.model_class(
                ).objects.get(id=job_object.enqueued_object_id)
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
        try:
            enqueued_object_type = job_object.enqueued_object_type
            enqueued_object = job_object.enqueued_object

            return mark_safe('<a href="{}">{}</a>'.format(
                reverse("admin:{}_{}_change".format(
                    enqueued_object_type.app_label,
                    enqueued_object_type.model),
                    args=(enqueued_object.id,)),
                str(enqueued_object)))
        except:
            return '-'

    enqueued_object_link.short_description = "Enqueued Object"

    def lookup_allowed(self, key, value):
        if key in (
            'id__in',
            'running_state',
            'workflow_node__job_queue__name',
            'running_state__in',
        ):
            return True

        return super(JobAdmin, self).lookup_allowed(key, value)
