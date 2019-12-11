import argparse
from workflow_engine.client_settings import configure_worker_app
from celery import Celery
from workflow_engine.signatures import (
    process_pbs_id_signature,
    process_running_signature,
    process_finished_execution_signature,
    process_failed_execution_signature
)


_RESPONSE_TIMEOUT = 10


def send_queued(task_id, pbs_id):
    r = process_pbs_id_signature.delay(task_id, pbs_id)

    return r.wait(_RESPONSE_TIMEOUT)

def send_running(task_id):
    r = process_running_signature.delay(task_id)

    return r.wait(_RESPONSE_TIMEOUT)

def send_finished(task_id):
    r = process_finished_execution_signature.delay(task_id)

    return r.wait(_RESPONSE_TIMEOUT)

def send_failed_execution(task_id):
    r = process_failed_execution_signature.delay(task_id, fail_now= True)

    return r.wait(_RESPONSE_TIMEOUT)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--action")
    parser.add_argument("--pbs_id")
    parser.add_argument("task_id")
    parser.add_argument("app_name")

    args = parser.parse_args()

    app = Celery(args.app_name)
    configure_worker_app(app, args.app_name)

    if args.action == 'queued':
        print(send_queued(args.task_id, args.pbs_id))
    elif args.action == 'running':
        print(send_running(args.task_id))
    elif args.action == 'finished':
        print(send_finished(args.task_id))
    elif args.action == 'failed_execution':
        print(send_failed_execution(args.task_id))
