from django.conf import settings
import django; django.setup()
import os
import celery
from workflow_engine.models.task import Task
import traceback
from workflow_engine.workflow_controller import WorkflowController
import logging
from workflow_engine.celery.result_tasks \
    import process_failed_execution, process_finished_execution


_log = logging.getLogger('workflow_engine.celery.worker_tasks')


SUCCESS_EXIT_CODE = 0
ERROR_EXIT_CODE = 1
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
            workflow_node_id, enqueued_object_id, priority)
    except Exception as e:
        report_exception(e)
        return -1

    return job.id


@celery.shared_task(bind=True)
def queue_job(self, job_ids):
    WorkflowController.set_jobs_for_run_by_id(job_ids)


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
def run_normal(self, full_executable, task_id, logfile):
    _log.info('run_normal')
    exit_code = os.system(full_executable)

    if exit_code == SUCCESS_EXIT_CODE:
        process_finished_execution(task_id).apply_async((task_id))

        with open(logfile, "a") as log:
            log.write("SUCCESS - execution finished successfully for task " + str(task_id))

    else:
        process_failed_execution.apply_async(
            (task_id,),
            queue=settings.RESULT_MESSAGE_QUEUE_NAME)

        with open(logfile, "a") as log:
            log.write("FAILURE - execution failed for task " + str(task_id))

    return exit_code


@celery.shared_task(bind=True)
def kill_job(self, job_id):
    WorkflowController.kill_job(job_id)


@celery.shared_task(bind=True)
def cancel_task(self, use_pbs, p_id):
    raise Exception("unimplemented")
