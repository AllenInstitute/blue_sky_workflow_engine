#!/usr/bin/env python
import sys
import logging
from workflow_client.ingest_client import IngestClient
from workflow_client.client_settings import settings

_log = logging.getLogger('workflow_client.pbs_execution_finish')

FIRST_ARG = -2 
SECOND_ARG = -1 
SUCCESS_EXIT_CODE = 0
ERROR_EXIT_CODE = 1

def set_exit_state(exit_code, task_id):
    host = settings.MESSAGE_QUEUE_HOST
    port = settings.MESSAGE_QUEUE_PORT
    user = settings.MESSAGE_QUEUE_USER
    password = settings.MESSAGE_QUEUE_PASSWORD
    exchange = ''
    queue = settings.CELERY_MESSAGE_QUEUE_NAME

    with IngestClient(host, port, user, password, exchange, queue) as ic:
        if exit_code == SUCCESS_EXIT_CODE:
            state='FINISHED_EXECUTION' 
        else:
            state='FAILED_EXECUTION'

        ic.send('%s,%d' % (state, task_id))

def config_logging():
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('workflow_client').setLevel(logging.INFO)
    logging.getLogger('workflow_client').addHandler(console)
    logging.getLogger('pika').setLevel(logging.DEBUG)
    logging.getLogger('pika').addHandler(console)

if __name__ == '__main__':
    config_logging()
    exit_code = int(sys.argv[FIRST_ARG])
    task_id = int(sys.argv[SECOND_ARG])

    set_exit_state(exit_code, task_id)

