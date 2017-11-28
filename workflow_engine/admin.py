from django.contrib import admin
from workflow_engine.models.executable import Executable
from workflow_engine.models.job_queue import  JobQueue
from workflow_engine.models.run_state import RunState
from workflow_engine.models.datafix import Datafix
from workflow_engine.models.well_known_file \
    import WellKnownFile, FileRecord
from workflow_engine.models.workflow import  Workflow
from workflow_engine.models.task import Task
from workflow_engine.models.workflow_node import WorkflowNode
from workflow_engine.models.job import Job


# Register your models here.
admin.site.register(Datafix)
admin.site.register(Executable)
admin.site.register(FileRecord)
admin.site.register(Job)
admin.site.register(JobQueue)
admin.site.register(RunState)
admin.site.register(Task)
admin.site.register(WellKnownFile)
admin.site.register(Workflow)
admin.site.register(WorkflowNode)
