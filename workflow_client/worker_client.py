from celery import Celery
import os
from workflow_client.reply_client import ReplyClient
from workflow_client.server_command \
    import server_command, check_environment_variables
from celery.utils.log import get_task_logger

MESSAGE_QUEUE_HOST = os.getenv('MESSAGE_QUEUE_HOST', 'message_queue')
message_queues = {
    'spark': 'spark_at_em_imaging_workflow',
    'pbs': 'pbs_at_em_imaging_workflow',
    'manual': 'manual_at_em_imaging_workflow',
    'local': 'at_em_imaging_workflow',
    'celery': 'celery_at_em_imaging_workflow'
}
MESSAGE_QUEUE_NAME = os.environ.get(
    'BLUE_SKY_WORKER_NAME',
    message_queues['local'])
CELERY_MESSAGE_QUEUE_NAME = message_queues['celery']
MESSAGE_QUEUE_USER = 'blue_sky_user'
MESSAGE_QUEUE_PASSWORD = 'blue_sky_user'
MESSAGE_QUEUE_PORT = int(os.environ.get('AMQP_PORT', '5672'))

_log = get_task_logger('execution_runner')
_log.info('Connecting to: %s %d' % (MESSAGE_QUEUE_HOST, MESSAGE_QUEUE_PORT))

app = Celery('workflow_client.worker_client',
             backend='rpc://',
             broker='pyamqp://' + str(MESSAGE_QUEUE_USER) + ':' + \
             str(MESSAGE_QUEUE_PASSWORD) + '@' + MESSAGE_QUEUE_HOST + ':' + \
             str(MESSAGE_QUEUE_PORT) + '//')
app.conf.task_default_queue = CELERY_MESSAGE_QUEUE_NAME

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


@app.task
def run_server_command(command):
    _log.info('run server command')
    check_environment_variables()

    qmaster_host = os.environ.get('QMASTER_HOST', 'qmaster')
    qmaster_username = os.environ['QMASTER_USERNAME']
    qmaster_password = os.environ['QMASTER_PASSWORD']
    qmaster_port = int(os.environ.get('QMASTER_PORT', '22'))
    _log.info('qmaster cred: %s %s %s %d' % (
        qmaster_host,
        qmaster_username,
        qmaster_password,
        qmaster_port))
       
    stdout_message, stderr_message = \
        server_command(qmaster_host,
                       qmaster_port,
                       qmaster_username,
                       qmaster_password,
                       command)

    _log.info('qmaster output: %s' % (str(stdout_message)))
    _log.info('qmaster error: %s' % (str(stderr_message)))
    
    return stdout_message

@app.task
def run_pbs(full_executable, task_id):
    _log.info('run_pbs')
    exit_code = SUCCESS_EXIT_CODE

    try:
        stdout_message = run_server_command(full_executable)
        _log.info('PBS STDOUT: ' + str(stdout_message))

        pbs_id = stdout_message[FIRST].strip().replace(
            ".corp.alleninstitute.org", "")
        # pbs_id = stdout_message[FIRST].strip()

        _log.info('pbs task: %s, pbs id: %s' % (str(task_id), str(pbs_id)))
        publish_message('PBS_ID', task_id, pbs_id)

    except Exception as e:
        report_exception('FAILED_EXECUTION', e)
        exit_code = ERROR_EXIT_CODE
        publish_message('FAILED_EXECUTION', task_id)

    return exit_code

@app.task
def run_normal(full_executable, task_id, logfile):
    _log.info('run_normal')
    exit_code = os.system(full_executable)

    if exit_code == SUCCESS_EXIT_CODE:
        publish_message('FINISHED_EXECUTION', task_id)

        with open(logfile, "a") as log:
            log.write("SUCCESS - execution finished successfully for task " + str(task_id))

    else:
        publish_message('FAILED_EXECUTION', task_id)

        with open(logfile, "a") as log:
            log.write("FAILURE - execution failed for task " + str(task_id))

    return exit_code

@app.task
def publish_message(body, task_id, optional_body=None):
    with ReplyClient(
        MESSAGE_QUEUE_HOST,
        int(MESSAGE_QUEUE_PORT),
        MESSAGE_QUEUE_USER,
        MESSAGE_QUEUE_PASSWORD,
        '',
        CELERY_MESSAGE_QUEUE_NAME) as ic:
        if optional_body is not None:
            ic.send(body + ',' + str(task_id) + ',' + str(optional_body))
        else:
            ic.send(body + ',' + str(task_id))
        

@app.task
def cancel_task(use_pbs, p_id):
    if use_pbs:
        try:
            pbs_id = p_id
            executable = 'qdel ' + str(pbs_id)
            run_server_command(executable)
        except Exception as e:
            report_exception('something went wrong', e)


@app.task
def run_celery_task(full_executable, task_id, logfile, use_pbs):
    _log.info('run_celery_task: (use_pbs=%s)' % (str(use_pbs)))
    exit_code = SUCCESS_EXIT_CODE

    try:
        publish_message('RUNNING', task_id)

        if(use_pbs):
            _log.info('PBS: %s' % (full_executable))
            exit_code = run_pbs(full_executable, task_id)
        else:
            _log.info('run normal: %s' % (full_executable))
            exit_code = run_normal(full_executable, task_id, logfile)

    except Exception as e:
        exit_code = ERROR_EXIT_CODE
        report_exception('run_celery_task error %s' % (task_id), e)
        publish_message('FAILED_EXECUTION', task_id)

    _log.info('run_celery_task exit code %s' % (str(exit_code)))

    return exit_code

