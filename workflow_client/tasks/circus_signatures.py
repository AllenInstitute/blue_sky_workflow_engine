from celery import signature
#from django.conf import settings

_PRIORITY_HIGH=6
_PRIORITY_NORMAL=5
_PRIORITY_LOW=4


submit_task_signature = signature(
    'workflow_engine.celery.circus_tasks.submit_worker_task')
submit_task_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    priority=_PRIORITY_NORMAL,
    retry=False,
    ignore_result=False
)


kill_task_signature = signature(
    'circus_test.kill_task')
kill_task_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    priority=_PRIORITY_HIGH,
    retry=False,
    ignore_result=False
)


task_stdout_signature = signature(
    'circus_test.task_stdout')
task_stdout_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    priority=_PRIORITY_NORMAL,
    retry=False,
    ignore_result=False
)


task_stderr_signature = signature(
    'circus_test.task_stderr')
task_stderr_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    priority=_PRIORITY_NORMAL,
    retry=False,
    ignore_result=False
)


check_status_signature = signature(
    'workflow_engine.check_circus_status')
check_status_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    priority=_PRIORITY_LOW,
    retry=False,
    ignore_result=False
)


check_remote_status_signature = signature(
    'workflow_engine.check_remote_status')
check_status_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    soft_time_limit=30,
    time_limit=60,
    expires=45,
    priority=_PRIORITY_LOW,
    retry=False,
    ignore_result=False
)


inspect_signature = signature(
    'workflow_engine.inspect_circus').set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    priority=_PRIORITY_NORMAL,
    retry=False,
    ignore_result=False
)


failed_execution_handler_signature = signature(
    'workflow_engine.celery.error_handler.failed_execution_handler')
failed_execution_handler_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    priority=_PRIORITY_NORMAL,
    retry=False,
    ignore_result=False
)
