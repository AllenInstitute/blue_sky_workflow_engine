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
import celery
from kombu import Exchange, Queue, binding
import django; django.setup()
from django.core.exceptions import ObjectDoesNotExist
from workflow_client.celery_run_consumer \
    import run_workflow_node_jobs_by_id
from workflow_client.client_settings \
    import load_settings_yaml, config_object
import logging
import traceback


_log = logging.getLogger('workflow_engine.celery.workflow_tasks')


def get_task_strategy_by_task_id(task_id):
    try:
        task = Task.objects.get(id=task_id)
        strategy = task.get_strategy()
    except Exception as e:
        _log.error(
            'Something went wrong: ' + (traceback.print_exc(e)))
    
    return (task, strategy)


@celery.shared_task(bind=True)
def process_running(self, task_id):
    (task, strategy) = get_task_strategy_by_task_id(task_id)
    # strategy.running_task(task)

@celery.shared_task(bind=True)
def process_finished_execution(self, task_id):
    (task, strategy) = get_task_strategy_by_task_id(task_id)
    strategy.finish_task(task)
    run_workflow_node_jobs_by_id.apply_async(
        (task.job.workflow_node.id,),
        queue='workflow')


@celery.shared_task(bind=True)
def process_failed_execution(self, task_id):
    (task, strategy) = get_task_strategy_by_task_id(task_id)
    strategy.fail_execution_task(task)
    run_workflow_node_jobs_by_id.apply_async(
        (task.job.workflow_node.id,),
        queue='workflow')


@celery.shared_task(bind=True)
def process_pbs_id(self, task_id, pbs_id):
    # TODO: move to task as set_pbs_id
    try:
        (task, _) = get_task_strategy_by_task_id(task_id)
        task.set_pbs_id(pbs_id)
    except ObjectDoesNotExist:
        _log.warn(
            "Task {} for PBS id {} does not exist",
            task_id,
            pbs_id)


def configure_queues(app, name):
    workflow_engine_exchange = Exchange(name, type='direct')

    run_routes = [
        binding(workflow_engine_exchange, routing_key='run')
    ]

    result_routes = [
        binding(workflow_engine_exchange, routing_key='result')
    ]

    null_routes = [binding(workflow_engine_exchange,
                               routing_key='null')]

    app.conf.task_queues = (
        Queue('run', run_routes),
        Queue('result', result_routes),
        Queue('null', null_routes))


def route_task(name, args, kwargs, options, task=None, **kw):
    task_name = '.'.split(name)[-1]

    if task_name in [ 
        'run_task',
        'run_workflow_node_jobs_by_id' ]:
        return { 'queue': 'workflow' }
    elif task_name in { 
        'process_running',
        'process_finished_execution',
        'process_failed_execution',
        'process_pbs_id',
        'success',
        'fail' }:
        return { 'queue': 'result' }
    else:
        return { 'queue': 'null' }


def configure_result_app(app, app_name):
    settings = load_settings_yaml()
    app.config_from_object(config_object(settings))

    configure_queues(app, app_name)
    app.conf.task_routes = [route_task]


# circular imports
from workflow_engine.models.task import Task
