from workflow_engine.models.task import Task
from rest_framework.serializers import ModelSerializer
from rest_framework.fields import DateTimeField


class TaskMonitorSerializer(ModelSerializer):
    start_run_time = DateTimeField(format='iso-8601')
    end_run_time = DateTimeField(format='iso-8601')
    class Meta:
        model = Task
        fields = '__all__'