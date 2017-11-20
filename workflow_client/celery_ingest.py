from workflow_client.client_settings import settings
from workflow_client.celery_ingest_consumer import \
    run_task, ingest_task, success, fail, on_raw_message

def ingest(app, workflow, body):
    r = ingest_task.apply_async(
        ('fred', body,),
        exchange=app+'_ingest',
        queue='ingest',
        link=success.s(),
        link_error=fail.s())

    print(r.get(on_message=on_raw_message,
                propagate=False))

def run_strategy(app, workflow, body):
    r = run_task.apply_async(
        ('fred', body,),
        exchange=app,
        queue='pbs',
        link=success.s(),
        link_error=fail.s())

    print(r.get(on_message=on_raw_message,
                propagate=False))

if __name__ == '__main__':
    for i in range(0, 5):
        ingest('at_em_imaging_workflow_ingest',
               'em_montage',
               'this is a test %d' % (i))
    for i in range(0, 5):
        run_strategy('at_em_imaging_workflow',
                     'lens_correction.step1',
                     'this is a test %d' % (i))
