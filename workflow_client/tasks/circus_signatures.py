from celery import signature
#from django.conf import settings

submit_task_signature = signature(
    'workflow_engine.celery.circus_tasks.submit_worker_task')
submit_task_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    exchange='blue_sky',
    routing_key='circus',
    queue='circus',
    ignore_result=False)

kill_task_signature = signature(
    'circus_test.kill_task')
kill_task_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    exchange='blue_sky',
    routing_key='circus',
    queue='circus',
    ignore_result=False)

task_stdout_signature = signature(
    'circus_test.task_stdout')
task_stdout_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    exchange='blue_sky',
    routing_key='circus',
    queue='circus',
    ignore_result=False)

task_stderr_signature = signature(
    'circus_test.task_stderr')
task_stderr_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    exchange='blue_sky',
    routing_key='circus',
    queue='circus',
    ignore_result=False)

check_status_signature = signature(
    'workflow_engine.check_circus_status')
check_status_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    exchange='blue_sky',
    routing_key='circus',
    queue='circus',
    ignore_result=False)

check_remote_status_signature = signature(
    'workflow_engine.check_remote_status')
check_status_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    exchange='blue_sky',
    routing_key='circus',
    queue='circus',
    ignore_result=False)

inspect_signature = signature(
    'workflow_engine.inspect_circus').set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    exchange='blue_sky',
    routing_key='circus',
    queue='circus',
    ignore_result=False)

failed_execution_handler_signature = signature(
    'workflow_engine.celery.error_handler.failed_execution_handler')
failed_execution_handler_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    # exchange=_EXCHANGE,
    routing_key='result',
    queue='result')
