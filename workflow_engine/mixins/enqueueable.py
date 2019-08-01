from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
import os

class Enqueueable(models.Model):
    ''' An enqueueable model object may be used as an :term:`enqueued object`
    in a :term:`workflow`.
    '''

    jobs = GenericRelation(
        'workflow_engine.Job',
        content_type_field='enqueued_object_type',
        object_id_field='enqueued_object_id')
    ''' Enqueueable models in a Blue Sky application
        are automatically associated to workflow :term:`jobs<job>`
    '''

    tasks = GenericRelation(
        'workflow_engine.Task',
        content_type_field='enqueued_task_object_type',
        object_id_field='enqueued_task_object_id')
    ''' Enqueueable models in a Blue Sky application
        are automatically associated to workflow :term:`tasks<task>`
    '''

    class Meta:
        abstract = True

    def content_type_string(self):
        ''' Convenience method to get the name of the model for use in paths.
        '''
        return str(ContentType.objects.get_for_model(self)).replace(' ', '_')

    def storage_basename(self):
        ''' Override to change the name of the storage directory for an enqueued
        object.
        '''
        return self.id

    def get_storage_directory(self, base_storage_directory=None):
        ''' Override for a custom :term:`storage directory` .
        Defaults to a path based on the base file path, content type and id
        '''
        if base_storage_directory is None:
            base_storage_directory = settings.BASE_FILE_PATH

        return os.path.join(
            base_storage_directory,
            self.content_type_string(),
            self.storage_basename())
