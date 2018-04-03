from workflow_client.server_command import server_command
from django.conf import settings
import django; django.setup()
import os
import celery
from workflow_engine.models.task import Task
import traceback
from workflow_engine.workflow_controller import WorkflowController
import logging
from workflow_engine.celery.workflow_tasks import process_running,\
    process_failed_execution, process_pbs_id, process_finished_execution


_log = logging.getLogger('workflow_client.worker_client')


SUCCESS_EXIT_CODE = 0
ERROR_EXIT_CODE = 1
ZERO = 0
FIRST = 0


def report_exception(msg, e):
    #msg_string = '%s: %s' % (msg, str(e))
    mess = str(e) + ' - ' + str(traceback.format_exc())
    _log.error(mess)


def report_error(msg):
    print(msg)
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
def run_server_command(self,command):
    _log.info('run server command')

    _log.info(
        'qmaster cred: %s %s %s %d',
        settings.QMASTER_HOST,
        settings.QMASTER_USERNAME,
        '*',
        settings.QMASTER_PORT)
       
    stdout_message, stderr_message = \
        server_command(settings.QMASTER_HOST,
                       settings.QMASTER_PORT,
                       settings.QMASTER_USERNAME,
                       settings.QMASTER_PASSWORD,
                       command)

    _log.info('qmaster output: %s', str(stdout_message))
    _log.info('qmaster error: %s', str(stderr_message))

    return stdout_message

@celery.shared_task(bind=True)
def run_pbs(self, full_executable, task_id):
    _log.info('run_pbs')
    exit_code = SUCCESS_EXIT_CODE

    try:
        stdout_message = run_server_command(full_executable)
        _log.info('PBS STDOUT: ' + str(stdout_message))

        pbs_id = stdout_message[FIRST].strip().split('.')[FIRST]

        _log.info('pbs task: %s, pbs id: %s' % (str(task_id), str(pbs_id)))
        process_pbs_id.apply_async(
            (task_id, pbs_id),
            queue='result')

    except Exception as e:
        report_exception('FAILED_EXECUTION', e)
        exit_code = ERROR_EXIT_CODE
        #publish_message('FAILED_EXECUTION', task_id)
        process_failed_execution.apply_async(
            (task_id,),
            queue='result')

    return exit_code # TODO, this doesn't make sense as a return code

@celery.shared_task(bind=True)
def run_normal(self, full_executable, task_id, logfile):
    _log.info('run_normal')
    exit_code = os.system(full_executable)

    if exit_code == SUCCESS_EXIT_CODE:
        #publish_message('FINISHED_EXECUTION', task_id)
        process_finished_execution(task_id).apply_async((task_id))

        with open(logfile, "a") as log:
            log.write("SUCCESS - execution finished successfully for task " + str(task_id))

    else:
        #publish_message('FAILED_EXECUTION', task_id)
        process_failed_execution.apply_async((task_id))

        with open(logfile, "a") as log:
            log.write("FAILURE - execution failed for task " + str(task_id))

    return exit_code


@celery.shared_task(bind=True)
def kill_job(self, job_id):
    WorkflowController.kill_job(job_id)


@celery.shared_task(bind=True)
def cancel_task(self, use_pbs, p_id):
    if use_pbs:
        try:
            pbs_id = p_id
            executable = 'qdel ' + str(pbs_id)
            run_server_command(executable)
        except Exception as e:
            report_exception('something went wrong', e)


@celery.shared_task(bind=True)
def run_celery_task(self, full_executable, task_id, logfile, use_pbs):
    _log.info('run_celery_task: (use_pbs=%s)', str(use_pbs))
    exit_code = SUCCESS_EXIT_CODE

    try:
        #publish_message('RUNNING', task_id)
        process_running.apply_async(
            (task_id,),
            queue='result')

        if(use_pbs):
            _log.info('PBS: %s', full_executable)
            exit_code = run_pbs(full_executable, task_id)
        else:
            _log.info('run normal: %s', full_executable)
            exit_code = run_normal(full_executable, task_id, logfile)

    except Exception as e:
        exit_code = ERROR_EXIT_CODE
        report_exception('run_celery_task error %s' % (task_id), e)
        process_failed_execution.apply_async(
            (task_id,),
            queue='result')

    _log.info('run_celery_task exit code %s', str(exit_code))

    return exit_code

