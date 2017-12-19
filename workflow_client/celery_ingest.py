# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2017. Allen Institute. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Redistributions for commercial purposes are not permitted without the
# Allen Institute's written permission.
# For purposes of this license, commercial purposes is the incorporation of the
# Allen Institute's software into anything for which you will charge fees or
# other compensation. Contact terms@alleninstitute.org for commercial licensing
# opportunities.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
from workflow_client.celery_ingest_consumer import \
    run_task, ingest_task, success, fail, on_raw_message
import logging
import sys
import os


_log = logging.getLogger('workflow_client.celery_ingest')
logging.basicConfig(level=logging.INFO)
_log.setLevel(logging.INFO)

def ingest(app, workflow, body, tags):
    _log.info('sending ingest ' + app + ' ' + workflow + ' ' + str(body))

    r = ingest_task.apply_async(
        (workflow, body,tags),
        exchange=app+'_ingest',
        routing_key=workflow,
        link=success.s(),
        link_error=fail.s())

    return r.get(
        on_message=on_raw_message,
        propagate=False)

def run_strategy(app, workflow_name, body):
    r = run_task.apply_async(
        (workflow_name, body,),
        exchange=app,
        queue='pbs',
        link=success.s(),
        link_error=fail.s())

    return r.get(
        on_message=on_raw_message,
        propagate=False)

if __name__ == '__main__':
    from workflow_engine.import_class import import_class
    import simplejson as json

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

    if 'ReferenceSetTest' == fix_option:
        # lens_correction_new_body_data.pop('reference_set_id', None) # doesn't have this`
        body_data['acquisition_data']['microscope_type'] = 'TEM'
        body_data['manifest_path'] = \
            "/allen/aibs/pipeline/image_processing/volume_assembly/lc_test_data/Wij_Set_594451332/594089217_594451332/_trackem_20170502174048_295434_5LC_0064_01_20170502174047_reference_0_.txt"
        body_data['storage_directory'] = \
            "/allen/aibs/pipeline/image_processing/volume_assembly/lc_test_data/Wij_Set_594451332/594089217_594451332"
        body_data['metafile'] = \
            "/allen/aibs/pipeline/image_processing/volume_assembly/dataimport_test_data/_metadata_20170829130146_295434_5LC_0064_01_redo_001050_0_.json"
    elif 'EMMontageSetTest' == fix_option:
        body_data['acquisition_data']['microscope_type'] = 'TEM'
        body_data['metafile'] = \
            "/allen/aibs/pipeline/image_processing/volume_assembly/dataimport_test_data/_metadata_20170829130146_295434_5LC_0064_01_redo_001050_0_.json"
    if 'ReferenceSet' == fix_option:
        # lens_correction_new_body_data.pop('reference_set_id', None) # doesn't have this`
        body_data['acquisition_data']['microscope_type'] = 'TEM'
        body_data['manifest_path'] = \
            "/allen/programs/celltypes/workgroups/em-connectomics/data/295434_5LC_0064_reimaging_03/20171004173254_reference/0/_trackem_20171004173254_295434_5LC_0064_reimaging_03_20171004173254_reference_0_.txt"
        body_data['storage_directory'] = \
            "/allen/programs/celltypes/workgroups/em-connectomics/data/295434_5LC_0064_reimaging_03/20171004173254_reference/0"
        body_data['metafile'] = \
            "/allen/programs/celltypes/workgroups/em-connectomics/data/295434_5LC_0064_reimaging_03/20171004173254_reference/0/_metadata_20171004173254_295434_5LC_0064_reimaging_03_20171004173254_reference_0_.json"
    elif 'EMMontageSet' == fix_option:
        body_data['acquisition_data']['microscope_type'] = 'TEM'
        body_data['metafile'] = \
            "/allen/programs/celltypes/workgroups/em-connectomics/data/295434_5LC_0064_reimaging_03/001047/0/_metadata_20171004191109_295434_5LC_0064_reimaging_03_001047_0_.json"
    else:
        pass

    ingest(app_key,
           workflow_name,
           body_data,
           [fix_option])

