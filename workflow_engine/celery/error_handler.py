import celery
from celery.result import AsyncResult

process_failed_execution_signature = celery.signature(
    'workflow_engine.celery.result_tasks.process_failed_execution')
process_failed_execution_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    # exchange=_EXCHANGE,
    routing_key='result',
    queue='result')

@celery.shared_task(
    name='workflow_engine.celery.error_handler.failed_execution_handler',
    bind=True
)
def failed_execution_handler(self, uuid, task_id):
    result = AsyncResult(uuid)
    exc = result.get(propagate=False)
    process_failed_execution_signature.delay(task_id)
