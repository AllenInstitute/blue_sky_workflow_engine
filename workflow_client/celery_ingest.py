#from workflow_client.client_settings import settings
from rendermodules.ingest.schemas \
    import example as em_2d_montage_body_data
from workflow_client.celery_ingest_consumer import \
    run_task, ingest_task, success, fail, on_raw_message
import logging
import sys


_log = logging.getLogger('workflow_client.celery_ingest')
logging.basicConfig(level=logging.INFO)
_log.setLevel(logging.INFO)

# They're currently very similar
lens_correction_new_body_data = em_2d_montage_body_data
# lens_correction_new_body_data.pop('reference_set_id', None) # doesn't have this`
lens_correction_new_body_data['manifest_path'] = \
    "/allen/aibs/pipeline/image_processing/volume_assembly/lc_test_data/Wij_Set_594451332/594089217_594451332/_trackem_20170502174048_295434_5LC_0064_01_20170502174047_reference_0_.txt"
lens_correction_new_body_data['storage_directory'] = \
    "/allen/aibs/pipeline/image_processing/volume_assembly/lc_test_data/Wij_Set_594451332/594089217_594451332"
lens_correction_new_body_data['metafile'] = \
    "/allen/aibs/pipeline/image_processing/volume_assembly/dataimport_test_data/_metadata_20170829130146_295434_5LC_0064_01_redo_001050_0_.json"
em_2d_montage_body_data['metafile'] = \
    "/allen/aibs/pipeline/image_processing/volume_assembly/dataimport_test_data/_metadata_20170829130146_295434_5LC_0064_01_redo_001050_0_.json"

def ingest(app, workflow, body):
    _log.info('sending ingest ' + app + ' ' + workflow + ' ' + str(body))

    r = ingest_task.apply_async(
        (workflow, body,),
        exchange=app+'_ingest',
        routing_key=workflow)
        #queue='ingest') #,
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
    workflow_name = sys.argv[-2]
    body = sys.argv[-1]

    if 'lens_correction_new' == workflow_name:
        body_data = lens_correction_new_body_data
    elif 'em_2d_montage' == workflow_name:
        body_data = em_2d_montage_body_data
    else:
        body_data = { 'message': 'ingest_example_data' }

    for i in range(0, 1):
        ingest('at_em_imaging_workflow',
               workflow_name,
               body_data)
    # for i in range(0, 5):
    #     run_strategy('at_em_imaging_workflow',
    #                  'lens_correction.step1',
    #                  'this is a test %d' % (i))
