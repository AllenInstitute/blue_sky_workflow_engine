# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2017-2019. Allen Institute. All rights reserved.
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
import django; django.setup()
from django.conf import settings
from workflow_engine.models import (
    Task,
    WorkflowNode
)
from workflow_engine.workflow_controller import WorkflowController
from django.core.exceptions import ObjectDoesNotExist
from workflow_client.client_settings import configure_worker_app
from celery.exceptions import SoftTimeLimitExceeded
import logging
import traceback
import celery


_log = logging.getLogger('workflow_engine.celery.workflow_tasks')


app = celery.Celery('workflow_engine.celery.workflow_tasks')
configure_worker_app(app, settings.APP_PACKAGE, 'workflow')
app.conf.imports = ()


@celery.signals.after_setup_task_logger.connect
def after_setup_celery_task_logger(logger, **kwargs):
    logging.config.dictConfig(settings.LOGGING)


# TODO: move this somewhere more general
def report_exception(msg, e):
    mess = str(e) + ' - ' + str(traceback.format_exc())
    _log.error(mess)


def report_error(msg):
    _log.error(msg)

#
# UI TASKS
#

@celery.shared_task(
    bind=True,
    name='workflow_engine.celery.workflow_tasks.create_job')
def create_job(self, workflow_node_id, enqueued_object_id, priority):
    try:
        job = WorkflowController.create_job(
            workflow_node_id,
            enqueued_object_id,
            priority)
    except SoftTimeLimitExceeded:
        report_exception('Soft Time Limit Exceeded')
        return -1
    except Exception as e:
        report_exception('Error creating job. ', e)
        return(str(e))

    if job is None:
        return -1

    return job.id


@celery.shared_task(
    bind=True,
    name='workflow_engine.celery.workflow_tasks.run_workflow_node_jobs_by_id'
)
def run_workflow_node_jobs_by_id(self, workflow_node_id):
    try:
        workflow_node = WorkflowNode.objects.get(id=workflow_node_id)
        WorkflowController.run_workflow_node_jobs(workflow_node)
    except ObjectDoesNotExist as e:
        _log.error(str(e) + ' - ' + str(traceback.format_exc()))
    except SoftTimeLimitExceeded:
        report_exception('Soft Time Limit Exceeded')
        return 'timeout'
    except Exception as e:
        _log.error(str(e) + ' - ' + str(traceback.format_exc()))
        return 'error'

    return 'done'


@celery.shared_task(bind=True)
def queue_job(self, job_ids):
    WorkflowController.set_jobs_for_run_by_id(job_ids)


@celery.shared_task(bind=True)
def enqueue_next_queue(self, job_id):
    WorkflowController.enqueue_next_queue_by_job_id(job_id)


#
# RESPONSES
#
def get_task_strategy_by_task_id(task_id):
    task = -1
    strategy = None

    try:
        task = Task.objects.get(id=task_id)
        strategy = task.get_strategy()
    except SoftTimeLimitExceeded:
        report_exception('Soft Time Limit Exceeded')
    except Exception as e:
        _log.error(
            'Something went wrong: ' + (traceback.print_exc(e)))

    return (task, strategy)

#
# REQUESTS
#
@celery.shared_task(bind=True)
def kill_job(self, job_id):
    WorkflowController.kill_job(job_id)
