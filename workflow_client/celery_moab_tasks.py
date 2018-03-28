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
from kombu import Exchange, Queue, binding
from workflow_engine.celery import settings
from workflow_client.client_settings \
    import load_settings_yaml, config_object
import logging
import django; django.setup()
from celery.canvas import group
import workflow_client.nb_utils.moab_api as moab_api
from workflow_client.nb_utils.task_monitor import read_task_dataframe
import re
from celery.states import SUCCESS
from workflow_client.celery_pbs_tasks import running


_log = logging.getLogger('workflow_client.celery_moab_tasks')


def moab_record_response(moab_state):
    if moab_state == 'Running':
        return running
    elif moab_state == 'Queued':
        return running
    elif moab_state == 'Completed':
        # need to check success/fail here
        return running
    else:
        return running


def get_running_task_df():
    # TODO: this is too heavy a query for long-term use
    task_url = \
        'http://{}:{}/workflow_engine/data'.format(
            settings.UI_HOST, settings.UI_PORT)
    task_df = read_task_dataframe(task_url)

    RUNNING_STATE_ID = 11  # TODO: from RunState

    return task_df.loc[lambda df: df.run_state == RUNNING_STATE_ID]


def get_moab_query_result(pbs_ids):
    return moab_api.moab_query(
        moab_api.moab_url(
            table='jobs',
            jobs=pbs_ids))


def custom_name_task_id(custom_name_string):
    return int(re.sub(r'^task_',
                      '',
                      custom_name_string,
                      count=1))


@celery.shared_task(bind=True, trail=True)
def check_pbs_status(self):
    running_task_df = get_running_task_df()

    moab_query_result = get_moab_query_result(
        list(running_task_df.pbs_id))

    _log.info([(
        r['name'],  # "<pbs_id>"
        r['customName'],  # "task_<workflow engine task id>"
        r['states']['state'],
        r['credentials']['user'])
        for r in moab_query_result])

    # TODO: do this in pandas
    workflow_task_moab_record = {
        custom_name_task_id(r['customName']): {  # task_id
            'pbs_id': int(r['name']),
            'pbs_run_state': r['states']['state']
        }
        for r in moab_query_result
    }
    _log.info(workflow_task_moab_record)

    self.update_state(state=SUCCESS)
    # see: http://docs.celeryproject.org/en/latest/reference/celery.result.html
    # and: https://github.com/celery/celery/issues/1171
    return group(
        moab_record_response(
            workflow_task_moab_record[task_id]['pbs_run_state']).s(
                workflow_task_moab_record[task_id]['pbs_id']).set(queue='result')
        for task_id in list(running_task_df.pbs_id)
        if task_id in workflow_task_moab_record.keys()
    )()


    #_log.info('sigs: ' + str(list(status_signatures)))

#     status_celery_tasks = group(
#         status_signature(task_id)
#         for (status_signature,task_id)
#         in status_signatures)
#     
#     _log.info(status_celery_tasks)
# 
#     return group(status_celery_tasks)
#     return group(
#         running.s(t).set(queue='result') for t in range(0,10))()


def configure_queues(app, name):
    workflow_engine_exchange = Exchange(name, type='direct')

    app.conf.task_queues = (
        Queue('moab', [binding(workflow_engine_exchange,
                               routing_key='moab')]),
        Queue('result', [binding(workflow_engine_exchange,
                                 routing_key='result')]),
        Queue('null', [binding(workflow_engine_exchange,
                               routing_key='null')]))


def route_task(name, args, kwargs, options, task=None, **kw):
    task_name = '.'.split(name)[-1]

    if task_name == 'check_pbs_status':
        return { 'queue': 'moab' }
    elif task_name in {
        'set_pbs_id',
        'set_running',
        'set_finished_execution',
        'set_failed_execution',
        'success',
        'fail' }:
        return { 'queue': 'result' }
    else:
        return { 'queue': 'null' }


def configure_moab_consumer_app(app, app_name):
    settings = load_settings_yaml()
    app.config_from_object(config_object(settings))

    configure_queues(app, app_name)
    app.conf.task_routes = [route_task]
