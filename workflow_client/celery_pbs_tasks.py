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
import logging
from kombu import Exchange, Queue, binding
from workflow_client.client_settings import load_settings_yaml, config_object
from workflow_engine.workflow_config import WorkflowConfig
from workflow_engine.import_class import import_class
import logging
import traceback
import django; django.setup()
from django.conf import settings
from workflow_engine.models.task import Task
from django.core.exceptions import ObjectDoesNotExist
from workflow_engine.models.run_state import RunState
from builtins import Exception
import time
from celery.canvas import group
from workflow_client.celery_ingest_consumer \
    import load_workflow_config
import workflow_client.nb_utils.moab_api as moab_api
from workflow_client.nb_utils.task_monitor import read_task_dataframe

_log = logging.getLogger('workflow_client.celery_pbs_consumer')


@celery.shared_task(bind=True)
def run_pbs(self):
    ret = 'OK'

    try: 
        ret = 'OK'
        time.sleep(1)
        self.update_state(state="QUEUED",
                          meta=ret)
        time.sleep(1)
        self.update_state(state="RUNNING",
                          meta=ret)
        time.sleep(1)
        self.update_state(state="EXECUTION_FINISHED   ",
                          meta=ret)
    except:
        ret = 'FAIL'
        self.update_state(state="FAIL",
                          meta=ret)

    return ret


@celery.shared_task(bind=True, trail=True)
def check_pbs_status(self):
    self.update_state(state="PBS_STATUS")

    task_url = 'http://ibs-timf-ux1:9002/workflow_engine/data'
    task_df = read_task_dataframe(task_url)
    running_task_ids = list(task_df.loc[lambda df: df.run_state == 11].id)

    result = moab_api.moab_query(
        moab_api.moab_url(
            table='jobs',
            jobs=running_task_ids))

    log_info = [(
        job['name'],
        job['customName'],
        job['states']['state'],
        job['credentials']['user']) for job in result]

    _log.info(log_info)
    

    # see: http://docs.celeryproject.org/en/latest/reference/celery.result.html
    return group(
        running.s(t) for t in range(0,10))()

def on_pbs_queued(msg):
    print('PBS QUEUED')


@celery.shared_task(bind=True)
def queued(self, msg):
    on_pbs_queued(msg)


def on_pbs_running(msg):
    print('PBS RUNNING')


@celery.shared_task(bind=True)
def running(self, msg):
    on_pbs_running(msg)

    return 'OK RUNNING'


def on_pbs_fail(msg):
    print('PBS FAIL')


@celery.shared_task(bind=True, trail=True)
def fail(self, msg):
    on_pbs_fail(msg)

    self.update_state('FAIL', meta=msg)


def on_pbs_success(msg):
    print('PBS SUCCESS')

@celery.shared_task(bind=True)
def success(self, msg):
    on_pbs_success(msg)


def on_raw_message(body):
    print(body)


def configure_pbs_app(app, app_name):
    settings = load_settings_yaml()
    app.config_from_object(config_object(settings))

    configure_queues(app, app_name)
    app.conf.task_routes = [route_task]

def configure_queues(app, name):
    pbs_routes = []

    pbs_exchange = Exchange('pbs_' + name, type='direct')
    result_exchange = Exchange('celery_' + name, type='direct')

    pbs_routes.append(
        binding(pbs_exchange,
                routing_key='pbs'))

    app.conf.task_queues = (
        Queue('pbs', pbs_routes),
        Queue('result', [binding(result_exchange, routing_key='result')]),
        Queue('null', [binding(result_exchange, routing_key='null')]))


def route_task(name, args, kwargs, options, task=None, **kw):
    task_name = '.'.split(name)[-1]

    if task_name in [ 'run_pbs',
                     'check_pbs_status',
                     'success',
                     'fail',
                     'running' ]:
        return { 'queue': 'pbs' }
#    elif task_name in { 'success', 'fail' }:
#        return { 'queue': 'result' }
    else:
        return { 'queue': 'null' }


def configure_pbs_consumer_app(app, app_name):
    configure_task_queues(app, app_name)
    app.conf.task_routes = [route_task]

try:
    app = celery.Celery('workflow_client.celery_pbs_consumer')
    configure_pbs_consumer_app(app, 'at_em_imaging_workflow')
except:
    pass
