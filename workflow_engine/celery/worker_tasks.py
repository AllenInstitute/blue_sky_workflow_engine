from workflow_engine.models import (
    Task,
    WorkflowNode
)
from workflow_engine.workflow_controller import WorkflowController
from django.core.exceptions import ObjectDoesNotExist
from workflow_engine.celery.signatures import (
    process_failed_execution_signature,
    process_finished_execution_signature
)
import logging
import traceback
import os
import celery


_log = logging.getLogger('workflow_engine.celery.worker_tasks')


ZERO = 0
FIRST = 0


# TODO: move this somewhere more general
def report_exception(msg, e):
    mess = str(e) + ' - ' + str(traceback.format_exc())
    _log.error(mess)


def report_error(msg):
    _log.error(msg)

#
# UI TASKS
#

@celery.shared_task(bind=True)
def create_job(self, workflow_node_id, enqueued_object_id, priority):
    try:
        job = WorkflowController.create_job(
            workflow_node_id,
            enqueued_object_id,
            priority)
    except Exception as e:
        report_exception('Error creating job. ', e)
        return -1

    return job.id


@celery.shared_task(bind=True)
def run_workflow_node_jobs_by_id(self, workflow_node_id):
    try:
        workflow_node = WorkflowNode.objects.get(id=workflow_node_id)
        WorkflowController.run_workflow_node_jobs(workflow_node)
    except ObjectDoesNotExist as e:
        _log.error(str(e) + ' - ' + str(traceback.format_exc()))

    return 'done'


@celery.shared_task(bind=True)
def queue_job(self, job_ids):
    WorkflowController.set_jobs_for_run_by_id(job_ids)


@celery.shared_task(bind=True)
def enqueue_next_queue(self, job_id):
    WorkflowController.enqueue_next_queue_by_job_id(job_id)


#
# RESPONSES
#
def get_task_strategy_by_task_id(task_id):
    try:
        task = Task.objects.get(id=task_id)
        strategy = task.get_strategy()
    except Exception as e:
        _log.error(
            'Something went wrong: ' + (traceback.print_exc(e)))
    
    return (task, strategy)

#
# REQUESTS
#
@celery.shared_task(bind=True)
def kill_job(self, job_id):
    WorkflowController.kill_job(job_id)
