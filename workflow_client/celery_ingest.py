#from workflow_client.client_settings import settings
import os
from workflow_client.celery_ingest_consumer import \
    run_task, ingest_task, success, fail, on_raw_message
from workflow_engine.import_class import import_class
    
import logging
import simplejson as json
import sys


_log = logging.getLogger('workflow_client.celery_ingest')
logging.basicConfig(level=logging.INFO)
_log.setLevel(logging.INFO)

def ingest(app, workflow, body, tags):
    _log.info('sending ingest ' + app + ' ' + workflow + ' ' + str(body))

    r = ingest_task.apply_async(
        (workflow, body,tags),
        exchange=app+'_ingest',
        routing_key=workflow)
        #queue='ingest') #,
        # link=success.s(),
        # link_error=fail.s())

    print(r.get(on_message=on_raw_message,
                propagate=False))

def run_strategy(app, workflow_name, body):
    r = run_task.apply_async(
        (workflow_name, body,),
        exchange=app,
        queue='pbs',
        link=success.s(),
        link_error=fail.s())

    print(r.get(on_message=on_raw_message,
                propagate=False))

if __name__ == '__main__':
    app_key = sys.argv[-4]  # e.g. 'at_em_imaging_workflow
    workflow_name = sys.argv[-3]  # e.g. '2d_em_montage'
    body_file = sys.argv[-2]
    fix_option = sys.argv[-1]

    _, file_extension = os.path.splitext(body_file)

    if 'json' == file_extension:
        with open(body_file) as f:
            body_data = json.loads(f.read())
    else:  # module name
        print("reading body message from module variable"  + body_file)
        body_data = import_class(body_file)

    if 'ReferenceSet' == fix_option:
        # lens_correction_new_body_data.pop('reference_set_id', None) # doesn't have this`
        body_data['manifest_path'] = \
            "/allen/aibs/pipeline/image_processing/volume_assembly/lc_test_data/Wij_Set_594451332/594089217_594451332/_trackem_20170502174048_295434_5LC_0064_01_20170502174047_reference_0_.txt"
        body_data['storage_directory'] = \
            "/allen/aibs/pipeline/image_processing/volume_assembly/lc_test_data/Wij_Set_594451332/594089217_594451332"
        body_data['metafile'] = \
            "/allen/aibs/pipeline/image_processing/volume_assembly/dataimport_test_data/_metadata_20170829130146_295434_5LC_0064_01_redo_001050_0_.json"
    elif 'EMMontageSet' == fix_option:
        body_data['metafile'] = \
            "/allen/aibs/pipeline/image_processing/volume_assembly/dataimport_test_data/_metadata_20170829130146_295434_5LC_0064_01_redo_001050_0_.json"
    else:
        pass

    ingest(app_key,
           workflow_name,
           body_data,
           [fix_option])

