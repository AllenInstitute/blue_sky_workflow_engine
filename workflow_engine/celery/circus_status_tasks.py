# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2019. Allen Institute. All rights reserved.
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
from workflow_engine.client_settings import configure_worker_app
import django; django.setup()
from django.conf import settings
from workflow_engine.models import Task
from celery.exceptions import SoftTimeLimitExceeded
from workflow_engine.tasks.circus_signatures import ( 
    check_remote_status_signature
)
import logging

_log = logging.getLogger('workflow_engine.celery.circus_status_tasks')
app_name = 'blue_sky'
worker_name = 'circus_status'

REMOTE_QUEUE = 'circus'
app = celery.Celery(app_name)
app.conf.imports = (
    'workflow_engine.celery.error_handler',
)
configure_worker_app(app, settings.APP_PACKAGE, 'circus_status')
app.conf.time_lmit=60
app.conf.soft_time_limit=45


def node_tasks_in_states(remote_queue, state_names):
    return Task.objects.filter(
        job__workflow_node__job_queue__executable__remote_queue=remote_queue,
        running_state__in=state_names)

def get_queued_and_running_task_dicts():
    tasks = node_tasks_in_states(REMOTE_QUEUE, ['QUEUED', 'RUNNING'])

    return [{
        'task_id': t.id,
        'workflow_state': t.running_state,
        'remote_id': t.pbs_id } for t in tasks]

@celery.shared_task(
    name='workflow_engine.check_circus_task_status',
    bind=True,
    trail=True)
def check_status(self):
    try:
        task_dicts = get_queued_and_running_task_dicts()

        _log.info('task dicts: ' + str(task_dicts))

        check_remote_status_signature.delay(task_dicts)
    except SoftTimeLimitExceeded:
        _log.warning('Soft Time Limit Exceeded')
        return 'timeout'
    except Exception as e:
        _log.error(e)

        return 'error'

    return 'success'
