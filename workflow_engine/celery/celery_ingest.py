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
from workflow_engine.signatures import ingest_signature
from workflow_engine.celery import settings
import celery
import logging
import os


_log = logging.getLogger('workflow_engine.celery_ingest')
logging.basicConfig(level=logging.INFO)
_log.setLevel(logging.INFO)

def ingest(app, workflow, body, tags):
    _log.info('sending ingest ' + app + ' ' + workflow + ' ' + str(body))

    result = ingest_signature.delay(
        workflow, body, tags)

    response_message = result.wait(10)

    return response_message


@celery.signals.after_setup_task_logger.connect
def after_setup_celery_task_logger(logger, **kwargs):
    os.environ['DEBUG_LOG'] = 'test_debug.log'
    logging.config.dictConfig(settings.LOGGING)

if __name__ == '__main__':
    message = {
        'log_level': 'ERROR',
        'acquisition_data': {
            'microscope_type': 'TEMCA',
            'microscope': 'temca5',
            'camera': {
                'camera_id': '49600128',
                'height': 3840,
                'width': 3840,
                'model': 'Ximea CB200MG'
            },
            'acquisition_time': '2018-03-08T03:07:19+00:00',
            'overlap': 0.12
        },
        'metafile': '/allen/programs/celltypes/production/incoming/wijem/247488_8R_Tape070C_05_reimaging_001319_0/_metadata_20180307190719_247488_8R_Tape070C_05_reimaging_001319_0_.json',
        'reference_set_id': None,
        'storage_directory': '/allen/programs/celltypes/production/incoming/wijem/247488_8R_Tape070C_05_reimaging_001319_0/',
        'section': {
            'specimen': '247488_8R',
            'z_index': 1319,
            'sample_holder': '001319'
        }
    }

    response = ingest('at_em_imaging_workflow',
           'em_2d_montage',
           message,
           ['EMMontageSet'])

    print("RESPONSE: " + str(response))

