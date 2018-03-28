#from workflow_client.reply_client import ReplyClient
from workflow_client.server_command import server_command
from django.conf import settings
from celery.utils.log import get_task_logger
import django; django.setup()
import os
import celery
from workflow_engine.models.task import Task
import traceback
from workflow_engine.workflow_controller import WorkflowController
from workflow_engine.models.job import Job


_log = get_task_logger('worker_client')


SUCCESS_EXIT_CODE = 0
ERROR_EXIT_CODE = 1
ZERO = 0
FIRST = 0


def report_exception(msg, e):
    msg_string = '%s: %s' % (msg, str(e))
    print(msg_string)
    _log.error(msg_string)


def report_error(msg):
    print(msg)
    _log.error(msg)

#
# UI TASKS
#

@celery.shared_task(bind=True)
def create_job(self, workflow_node_id, enqueued_object_id, priority):
    WorkflowController.create_job(
        workflow_node_id, enqueued_object_id, priority)


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


@celery.shared_task(bind=True)
def set_running(self, task_id):
    (task, strategy) = get_task_strategy_by_task_id(task_id)
    strategy.running_task(task)


@celery.shared_task(bind=True)
def set_finished_execution(self, task_id):
    (task, strategy) = get_task_strategy_by_task_id(task_id)
    strategy.finish_task(task)


@celery.shared_task(bind=True)
def set_failed_execution(self, task_id):
    (task, strategy) = get_task_strategy_by_task_id(task_id)
    strategy.fail_execution_task(task)


@celery.shared_task(bind=True)
def set_pbs_id(self, task_id, pbs_id):
    (task, _) = get_task_strategy_by_task_id(task_id)
    task.pbs_id = pbs_id # str(body_data[Command.PBS_ID])
    task.save()


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
        # pbs_id = stdout_message[FIRST].strip()

        _log.info('pbs task: %s, pbs id: %s' % (str(task_id), str(pbs_id)))
        #publish_message('PBS_ID', task_id, pbs_id)
        set_pbs_id.apply_async((task_id, pbs_id))

    except Exception as e:
        report_exception('FAILED_EXECUTION', e)
        exit_code = ERROR_EXIT_CODE
        #publish_message('FAILED_EXECUTION', task_id)
        set_failed_execution.apply_async((task_id))

    return exit_code # TODO, this doesn't make sense as a return code

@celery.shared_task(bind=True)
def run_normal(self, full_executable, task_id, logfile):
    _log.info('run_normal')
    exit_code = os.system(full_executable)

    if exit_code == SUCCESS_EXIT_CODE:
        #publish_message('FINISHED_EXECUTION', task_id)
        set_finished_execution.apply_async((task_id))

        with open(logfile, "a") as log:
            log.write("SUCCESS - execution finished successfully for task " + str(task_id))

    else:
        #publish_message('FAILED_EXECUTION', task_id)
        set_failed_execution.apply_async((task_id))

        with open(logfile, "a") as log:
            log.write("FAILURE - execution failed for task " + str(task_id))

    return exit_code

# @celery.shared_task(bind=True)
# def publish_message(self, body, task_id, optional_body=None):
#     with ReplyClient(
#         settings.MESSAGE_QUEUE_HOST,
#         int(settings.MESSAGE_QUEUE_PORT),
#         settings.MESSAGE_QUEUE_USER,
#         settings.MESSAGE_QUEUE_PASSWORD,
#         '',
#         settings.CELERY_MESSAGE_QUEUE_NAME) as ic:
#         if optional_body is not None:
#             ic.send(body + ',' + str(task_id) + ',' + str(optional_body))
#         else:
#             ic.send(body + ',' + str(task_id))


@celery.shared_task(bind=True)
def kill_job(self, job_id):
    Job.kill_job(job_id)


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
        set_running.apply_async((task_id))

        if(use_pbs):
            _log.info('PBS: %s', full_executable)
            exit_code = run_pbs(full_executable, task_id)
        else:
            _log.info('run normal: %s', full_executable)
            exit_code = run_normal(full_executable, task_id, logfile)

    except Exception as e:
        exit_code = ERROR_EXIT_CODE
        report_exception('run_celery_task error %s' % (task_id), e)
        #publish_message('FAILED_EXECUTION', task_id)
        set_failed_execution.apply_async((task_id))

    _log.info('run_celery_task exit code %s', str(exit_code))

    return exit_code

