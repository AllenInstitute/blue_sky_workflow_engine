from django.contrib import admin
from workflow_engine.models import (
    Executable,
    JobQueue,
    WellKnownFile,
    FileRecord,
    Workflow,
    Task,
    WorkflowNode,
    WorkflowEdge,
    Job,
    Configuration
)
from workflow_engine.admin.executable_admin import ExecutableAdmin
from workflow_engine.admin.job_queue_admin import JobQueueAdmin
from workflow_engine.admin.workflow_admin import WorkflowAdmin
from workflow_engine.admin.task_admin import TaskAdmin
from workflow_engine.admin.job_admin import JobAdmin
from workflow_engine.admin.workflow_node_admin import WorkflowNodeAdmin
from workflow_engine.admin.workflow_edge_admin import WorkflowEdgeAdmin
from workflow_engine.admin.well_known_file_admin import WellKnownFileAdmin
from workflow_engine.admin.configuration_admin import ConfigurationAdmin


# Register your models here.
admin.site.register(Executable, ExecutableAdmin)
admin.site.register(FileRecord)
admin.site.register(Job, JobAdmin)
admin.site.register(JobQueue, JobQueueAdmin)
admin.site.register(WellKnownFile, WellKnownFileAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Workflow, WorkflowAdmin)
admin.site.register(WorkflowNode, WorkflowNodeAdmin)
admin.site.register(WorkflowEdge, WorkflowEdgeAdmin)
admin.site.register(Configuration, ConfigurationAdmin)
