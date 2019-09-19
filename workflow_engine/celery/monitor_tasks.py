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
from workflow_engine.models import (
    WorkflowNode,
    Job
)
from workflow_engine.import_class import import_class
from workflow_client.client_settings import configure_worker_app
import pandas as pd
import itertools as it
from datetime import datetime
import json
import logging
import os


app = celery.Celery('workflow_engine.celery.monitor_tasks')
configure_worker_app(app, settings.APP_PACKAGE, 'broadcast')
app.conf.imports = [
    'workflow_engine.celery.monitor_tasks',
]
app.conf.imports.extend(settings.MONITOR_TASK_MODULES)


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


# TODO: move into utilities class
def count_node_jobs_in_state(node, run_state):
    return Job.objects.filter(
        workflow_node__job_queue__name=node,
        running_state=run_state,
        archived=False).count()


# TODO move into utilities class
def workflow_summary(workflow_object):
    wns = workflow_object.workflownode_set.filter(
        archived=False)

    counts = [{
        'node': node,
        'state': run_state,
        'count':  count_node_jobs_in_state(node, run_state) } 
        for (node, run_state) in it.product(
            (str(n) for n in wns),
            Job.get_run_state_names()) ]

    counts.extend([{
        'node': str(n),
        'state': 'BATCH_SIZE',
        'count': n.batch_size
    } for n in wns ])

    counts_df = pd.DataFrame.from_records(counts)

    totals = counts_df.groupby(by='node')['count'].sum()

    summary = {
        'run_states': counts_df.to_dict('records'),
        'totals': totals.to_dict()
    }
    
    return summary


def update_workflow_state_json():
#     v = workflow_view.monitor_workflow
#     f = APIRequestFactory()
#     r = f.get('/workflow_engine/workflows/monitor')
#     resp = v(r)
    # resp.render()
    result = {
        'success': True,
        'message': '',
        'payload': {}
    }

    # TODO: move this into payload
    result['nodes'] = []
    result['edges'] = []

    nodes = WorkflowNode.objects.all()

    for n in nodes:
        result['nodes'].append(str(n))

        for s in n.sources.filter(archived=False):
            result['edges'].append({
                'source': str(s),
                'target': str(n)
            })

    summary = workflow_summary(
        nodes[0]
    )

    result.update(summary)

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
        json.dump(result, o, indent=2)
 
    return 'OK'


def update_job_grid_json():
    try:
        job_grid_class = import_class(settings.JOB_GRID_CLASS)

        grid = job_grid_class()
        grid.query_workflow_objects()
        grid.query_enqueued_objects()
        grid.chunk_assignment_mapping()
        df = grid.generate_grid()

        json_dict = json.loads(df.to_json(orient='table'))
        json_dict['columns'] = grid.sorted_node_names()

        outfile = os.path.join(
            settings.STATIC_ROOT,
            'workflow_engine',
            'javascript',
            'job_grid_data.json'
        )

        with open(outfile, 'w') as f:
            json.dump(json_dict, f, indent=2)

        return 'OK'
    except:
        return 'FAIL'


append_extra_function(update_workflow_state_json)
if settings.JOB_GRID_CLASS:
    append_extra_function(update_job_grid_json)
