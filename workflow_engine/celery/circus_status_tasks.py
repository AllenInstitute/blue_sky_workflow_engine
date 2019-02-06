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
import os
from workflow_client.simple_router import SimpleRouter
import django; django.setup()
from workflow_engine.models import Task
from workflow_client.tasks.circus_signatures import ( 
    check_remote_status_signature
)
import logging

_log = logging.getLogger('workflow_engine.celery.circus_status_tasks')
app_name = 'blue_sky'
worker_name = 'circus_status'
broker_url='amqp://blue_sky_user:blue_sky_user@ibs-timf-ux1.corp.alleninstitute.org:9008'

@celery.signals.after_setup_task_logger.connect
def after_setup_celery_task_logger(logger, **kwargs):
    logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'class': 'logging.Formatter',
            'format': '%(asctime)s %(name)-15s %(levelname)-8s %(processName)-10s %(message)s'
        }
    },    
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'detailed',
            'filename': os.environ.get('DEBUG_LOG',
                                       'logs/debug.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'WARN',
            'propagate': True,
        },
        'blue_sky': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'workflow_engine': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'workflow_client': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'celery.task': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        }
    }
})

REMOTE_QUEUE = 'circus'
app = celery.Celery(
    app_name,
    backend='rpc://',
    broker=broker_url)
app.conf.imports = (
    'workflow_engine.celery.error_handler',
)
router = SimpleRouter(app_name)
app.conf.task_queues = router.task_queues('circus_status')
app.conf.task_routes = (
    router.route_task,
)


@celery.shared_task(
    name='workflow_engine.check_circus_task_status',
    bind=True,
    trail=True)
def check_status(self):
    tasks = Task.objects.filter(
        job__workflow_node__job_queue__executable__remote_queue=REMOTE_QUEUE,
        run_state__name__in=['QUEUED', 'RUNNING'])

    task_dicts = [{
        'task_id': t.id,
        'workflow_state': t.run_state.name,  # TODO: run_state
        'remote_id': t.pbs_id } for t in tasks]

    _log.info('task dicts: ' + str(task_dicts))

    check_remote_status_signature.delay(task_dicts)
