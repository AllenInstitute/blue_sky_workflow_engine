from django.contrib.contenttypes.fields import GenericRelation

class Enqueueable(object):
    jobs = GenericRelation(
        'workflow_engine.Job',
        content_type_field='enqueued_object_type',
        object_id_field='enqueued_object_id')
    tasks = GenericRelation(
        'workflow_engine.Task',
        content_type_field='enqueued_object_type',
        object_id_field='enqueued_object_id')
