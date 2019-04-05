from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
import os

class Enqueueable(models.Model):
    jobs = GenericRelation(
        'workflow_engine.Job',
        content_type_field='enqueued_object_type',
        object_id_field='enqueued_object_id')
    tasks = GenericRelation(
        'workflow_engine.Task',
        content_type_field='enqueued_task_object_type',
        object_id_field='enqueued_task_object_id')

    class Meta:
        abstract = True

    def content_type_string(self):
        return str(ContentType.objects.get_for_model(self)).replace(' ', '_')

    def storage_basename(self):
        return self.id

    def get_storage_directory(self, base_storage_directory=None):
        if base_storage_directory is None:
            base_storage_directory = settings.BASE_FILE_PATH

        return os.path.join(
            base_storage_directory,
            self.content_type_string(),
            self.storage_basename())
