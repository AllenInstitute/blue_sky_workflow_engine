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
from celery import Celery, shared_task 
from kombu import Exchange, Queue, binding
from workflow_client.client_settings import settings, config_object
from workflow_engine.workflow_config import WorkflowConfig
from workflow_engine.import_class import import_class
import logging
import os

_log = logging.getLogger('workflow_client.celery_ingest_consumer')

def load_workflow_config(yaml_file):
    workflow_config = WorkflowConfig.from_yaml_file(yaml_file)

    return { 
        workflow_spec.name: workflow_spec.state_list
        for workflow_spec in workflow_config['flows']
    }


def configure_task_queues(app, name, workflows):
    task_queues = []
    ingest_routes = []
    pbs_routes = []
    local_routes = []
    manual_routes = []

    ingest_exchange = Exchange(name + '_ingest', type='direct')
    strategy_exchange = Exchange(name + '_workflow', type='direct')
    result_exchange = Exchange('celery_' + name, type='direct')

    for wf in workflows.keys():
        ingest_routes.append(
            binding(ingest_exchange,
                    routing_key=wf))

    for wf in workflows.keys():
        for strat in workflows[wf]:
            pbs_routes.append(
                binding(strategy_exchange,
                        routing_key='%s.%s' % (wf, strat )))

    app.conf.task_queues = (
        Queue('ingest', ingest_routes),
        Queue('pbs', pbs_routes),
        Queue('result', [binding(result_exchange, routing_key='result')]),
        Queue('null', [binding(result_exchange, routing_key='null')]))

def route_task(name, args, kwargs, options, task=None, **kw):
        task_name = '.'.split(name)[-1]

        if task_name == 'ingest_task':
            return { 'queue': 'ingest' }
        elif task_name == 'run_task':
            return { 'queue': 'pbs' }
        elif task_name in set(['success', 'fail']):
            return { 'queue': 'result' }
        else:
            return { 'queue': 'null' }

def ingest_consumer(): 
    app_name = 'workflow_client.celery_ingest_consumer'
    app = Celery(app_name)
    app.config_from_object(config_object(settings))
    workflows = load_workflow_config(settings.WORKFLOW_CONFIG_YAML)
    configure_task_queues(app, 'at_em_imaging_workflow', workflows)
    app.conf.task_routes = [route_task]

    return app

app = ingest_consumer()

# if os.environ.get('DJANGO_SETTINGS_MODULE', None) is not None:
#     from django.conf import settings as django_settings
#     django_settings.configure()
#     app.autodiscover_tasks(lambda: django_settings.INSTALLED_APPS) 


@app.task(bind=True)
def ingest_task(self, workflow, message):
    ret = 'YAY'
 
    try: 
        _log.info('ingest ' + str(workflow) + ' ' + str(message))

        clz = import_class(
            'development.strategies.lens_correction_ingest.LensCorrectionIngest')
        ingest_strategy = clz()
        ret = ingest_strategy.ingest_message(message)
        self.update_state(state="SUCCESS")
    except e:
        self.update_state(state="FAILURE")
        ret = "YUCK" + str(e)

    return ret


@app.task(bind=True)
def run_task(self, name, args):
    ret = None

    try: 
        ret = 'Yay'
        self.update_state(state="SUCCESS")
    except:
        self.update_state(state="FAIL")

    return ret

@app.task
def success(msg):
    print(msg)

@app.task
def fail(uuid):
    # e = result.get(propagate=False)
    # print('Error: %s %s %s' % (uuid, e, e.traceback))
    print('error')

def on_raw_message(body):
    print(body)

