#from workflow_client.client_settings import settings
#from rendermodules.ingest.schemas import example as message_body_data
from workflow_client.celery_ingest_consumer import \
    run_task, ingest_task, success, fail, on_raw_message
import logging


_log = logging.getLogger('workflow_client.celery_ingest')
logging.basicConfig(level=logging.INFO)
_log.setLevel(logging.INFO)

message_body_data = {
    "reference_set_id": "DEADBEEF",
    "acquisition_data": {
    "microscope": "temca2",
        "camera": {
            "camera_id": "4450428",
            "height": 3840,
            "width": 3840,
            "model": "Ximea CB200MG"
        },
        "overlap": 0.07,
        "acquisition_time": "2017-08-29T13:01:46",
        "metafile": "/allen/aibs/pipeline/image_processing/volume_assembly/dataimport_test_data/_metadata_20170829130146_295434_5LC_0064_01_redo_001050_0_.json"
    }
}

def ingest(app, workflow, body):
    _log.info('sending ingest ' + app + ' ' + workflow + ' ' + str(body))

    r = ingest_task.apply_async(
        (workflow, body,),
        exchange=app+'_ingest',
        #routing_key=workflow,
        queue='ingest') #,
        # link=success.s(),
        # link_error=fail.s())

    print(r.get(on_message=on_raw_message,
                propagate=False))

def run_strategy(app, workflow, body):
    r = run_task.apply_async(
        ('lens_correction_new', body,),
        exchange=app,
        queue='pbs',
        link=success.s(),
        link_error=fail.s())

    print(r.get(on_message=on_raw_message,
                propagate=False))

if __name__ == '__main__':
    for i in range(0, 1):
        ingest('at_em_imaging_workflow_ingest',
               'lens_correction_new.apply_lens_correction_new',
               message_body_data)
    # for i in range(0, 5):
    #     run_strategy('at_em_imaging_workflow',
    #                  'lens_correction.step1',
    #                  'this is a test %d' % (i))
