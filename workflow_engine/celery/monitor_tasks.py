# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2018. Allen Institute. All rights reserved.
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
import celery
import django; django.setup()
from django.conf import settings
from workflow_engine.views import workflow_view
from rest_framework.test import APIRequestFactory
from workflow_engine.import_class import import_class
from datetime import datetime
import logging
import os


_log = logging.getLogger('workflow_engine.celery.monitor_tasks')

EXTRA_FUNCTIONS = []

def append_extra_function(fn):
    EXTRA_FUNCTIONS.append(fn)

@celery.shared_task(
    name='workflow_engine.broadcast.update_dashboard',
    bind=True, trail=True)
def update_dashboard(self):
    _log.info(datetime.now())

    for fn in EXTRA_FUNCTIONS:
        fn()

    return 'OK'


def update_workflow_state_json():
    v = workflow_view.monitor_workflow
    f = APIRequestFactory()
    r = f.get('/workflow_engine/workflows/monitor')
    resp = v(r)
    # resp.render()
 
    outfile = os.path.join(
        settings.STATIC_ROOT,
        'workflow_engine',
        'javascript',
        'monitor_out.js')
 
    try:
        os.makedirs(os.path.dirname(outfile))
    except:
        pass
 
    with open(outfile, 'w') as o:
        o.write(resp.content.decode('utf-8'))
 
    return 'OK'


def update_job_grid_json():
    job_grid_class = import_class(settings.JOB_GRID_CLASS)
    grid = job_grid_class()
    grid.query_workflow_objects()
    grid.query_enqueued_objects()

    df = grid.generate_grid()

    outfile = '/var/www/static/job_grid_data.json'

    df.to_json(outfile, orient='table')

    return 'OK'


append_extra_function(update_workflow_state_json)
append_extra_function(update_job_grid_json)
