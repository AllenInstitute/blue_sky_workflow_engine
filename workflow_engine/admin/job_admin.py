from django.contrib import admin
from workflow_engine.workflow_controller import WorkflowController
from workflow_engine.models.task import Task


def kill_jobs(modeladmin, request, queryset):
    kill_jobs.short_description = \
        "Kill jobs"

    for job in queryset:
        job.kill()


def start_jobs(modeladmin, request, queryset):
    start_jobs.short_description = \
        "Start jobs"

    job_ids = [item.id for item in queryset]
    WorkflowController.run_all_jobs(job_ids)


class TaskInline(admin.StackedInline):
    model = Task


class JobAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'enqueued_object_id',
        'get_enqueued_object_display',
        'start_run_time',
        'duration',
        'workflow',
        'workflow_node',
        'run_state',
        'task_ids',
        'archived'
        ]
    list_select_related = [
        'workflow_node',
        'workflow_node__workflow',
        'run_state']
    list_filter = [
        'workflow_node__workflow',
        'workflow_node',
        'run_state',
        'archived']
    actions = [kill_jobs, start_jobs]
    inlines = [TaskInline,]
