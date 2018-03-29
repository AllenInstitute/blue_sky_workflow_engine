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
import logging
from django.core.exceptions import ObjectDoesNotExist
from workflow_client.client_settings import load_settings_yaml, config_object
import traceback


_log = logging.getLogger('workflow_client.celery_run_consumer')


def do_running():
    pass

def send_running(ctask, t_id):
    ctask.update_state(
        'RUNNING',
        meta={'task_id': t_id })


def send_success(ctask, t_id):
    ctask.update_state(
        'SUCCESS',
        meta={'task_id': t_id })


def send_failure(ctask, t_id):
    ctask.update_state(
        'FAILURE',
        meta={'task_id': t_id })

# TODO: put this in task model, where it can still be mocked if necessary.
def get_current_task_by_id(tid):
    task = None

    try:
        task = Task.objects.get(id=tid)
    except ObjectDoesNotExist as e:
        _log.error('no object')
    except Exception as e:
        _log.error(e)

    return task


@celery.shared_task(bind=True)
def run_workflow_node_jobs_by_id(self, workflow_node_id):
    try:
        workflow_node = WorkflowNode.objects.get(id=workflow_node_id)
        WorkflowController.run_workflow_node_jobs(workflow_node)
    except ObjectDoesNotExist as e:
        _log.error(str(e) + ' - ' + str(traceback.format_exc()))


# TODO: change name to something like process task state
# Not sure if we still need name
@celery.shared_task(bind=True, soft_time_limit=10, time_limit=30)
def run_task(self, name, args):
    #_log.info(" [x] Received " + str(name) + ' ' + str(args))
    ret = 'OK'
    return ret

#     try:
#         state = args[0]
#         task_id = args[1]
# 
#         task = get_current_task_by_id(task_id)
#         strategy = task.get_strategy()
# 
#         if state == RunState.get_running_state().name:
#             pass
#             #strategy.running_task(task)
#         elif state == RunState.get_finished_execution_state().name:
#             pass
#             #strategy.finish_task(task)
#         elif state == RunState.get_failed_execution_state().name:
#             pass
#             #strategy.fail_execution_task(task)
#         elif state == 'PBS_ID':
#             task.pbs_id = str(args[2])
#             # task.save()
#             pass
# 
#         #send_running(self, task_id)
#         
#         ret = 'OK'
#         do_running()
#     except Exception as e:
#         _log.error(str(e) + ' ' + traceback.format_exc())
#         ret = 'FAIL'
#         #send_failure(self, task_id)
# 
#     #send_success(self, task_id)

#    return ret


def do_transition():
    pass


@celery.shared_task(bind=True)
def enqueue_next(self, msg):
    #do_transition()
    print(msg)


@celery.shared_task(bind=True)
def success(self, msg):
    print('Success! '  + msg)


@celery.shared_task(bind=True)
def fail(self, msg):
    # e = result.get(propagate=False)
    # print('Error: %s %s %s' % (uuid, e, e.traceback))
    print('error')


def do_timeout():
    pass

@celery.shared_task
def timeout(uuid):
    do_timeout()


def on_raw_message(body):
    print(body)


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
        # 'run_workflow_node_jobs_by_id'
        ]:
        return { 'queue': 'run' }
    elif task_name in { 
        'running',
        'set_running',
        'set_queued',
        'set_failed_execution',
        'success',
        'fail' }:
        return { 'queue': 'result' }
    else:
        return { 'queue': 'null' }


def configure_run_app(app, app_name):
    #settings = load_settings_yaml()
    #app.config_from_object(config_object(settings))

    configure_queues(app, app_name)
    app.conf.task_routes = [route_task]

# circular imports
from workflow_engine.models.task import Task
from workflow_engine.models.workflow_node import WorkflowNode
from workflow_engine.workflow_controller import WorkflowController
