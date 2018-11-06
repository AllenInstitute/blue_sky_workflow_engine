from django.contrib import admin
import django; django.setup()
from workflow_engine.models.executable import Executable
from workflow_engine.models.job_queue import  JobQueue
from workflow_engine.models.run_state import RunState
from workflow_engine.admin.executable_admin import ExecutableAdmin
from workflow_engine.admin.job_queue_admin import JobQueueAdmin
from workflow_engine.admin.workflow_admin import WorkflowAdmin
from workflow_engine.models.well_known_file \
    import WellKnownFile, FileRecord
from workflow_engine.models.workflow import  Workflow
from workflow_engine.models.task import Task
from workflow_engine.admin.task_admin import TaskAdmin
from workflow_engine.models.workflow_node import WorkflowNode
from workflow_engine.models.job import Job
from workflow_engine.models.configuration import Configuration
from workflow_engine.admin.job_admin \
    import JobAdmin
from workflow_engine.admin.workflow_node_admin \
    import WorkflowNodeAdmin
from workflow_engine.admin.well_known_file_admin import WellKnownFileAdmin
from workflow_engine.admin.configuration_admin import ConfigurationAdmin


# Register your models here.
# admin.site.register(Datafix)
admin.site.register(Executable, ExecutableAdmin)
admin.site.register(FileRecord)
admin.site.register(Job, JobAdmin)
admin.site.register(JobQueue, JobQueueAdmin)
admin.site.register(WellKnownFile, WellKnownFileAdmin)
admin.site.register(RunState)
admin.site.register(Task, TaskAdmin)
admin.site.register(Workflow, WorkflowAdmin)
admin.site.register(WorkflowNode, WorkflowNodeAdmin)
admin.site.register(Configuration, ConfigurationAdmin)
