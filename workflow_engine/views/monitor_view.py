from rest_pandas import PandasView
from workflow_engine.models.task import Task
from workflow_engine.serializers.task_monitor_serializer \
    import TaskMonitorSerializer


class MonitorView(PandasView):
    queryset = Task.objects.all()
    serializer_class = TaskMonitorSerializer