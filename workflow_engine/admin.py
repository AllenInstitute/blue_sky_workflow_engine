from django.contrib import admin
from workflow_engine.models import Executable, JobQueue, RunState, Workflow, \
 WellKnownFile, WorkflowNode, Job, Datafix, Task, FileRecord

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
