# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2017-2018. Allen Institute. All rights reserved.
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
from workflow_client.simple_router import SimpleRouter
import os
import yaml
import logging


_log = logging.getLogger('workflow_client.client_settings')


class settings_attr_dict(dict):
    __getattr__ = dict.get


_DEFAULT_SETTINGS_DICT = {
    'broker_url': 'pyamqp://blue_sky_user:blue_sky_user@message_queue:5672/',
    'result_backend': 'rpc://',
    'result_persistent': True,
    'task_serializer': 'json',
    'result_serializer': 'json',
    'result_expires': 3600, # 1 hour in seconds
    'broker_connection_timeout': 10,
    'broker_connection_retry': False,
    'soft_time_limit': 600,
    'time_limit': 2400,
    'accept_content': ['json'],
    'worker_prefetch_multiplier': 1,
    'timezone': 'US/Pacific',
    'enable_utc': True,
    'broker_transport_options': {
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 10,
        'interval_max': 30
    }
} 

def load_settings_yaml():
    settings_dict = _DEFAULT_SETTINGS_DICT

    try: 
        blue_sky_settings = os.environ.get(
            'BLUE_SKY_SETTINGS',
            'blue_sky_settings.yml'
        )

        with open(blue_sky_settings) as f:
            settings_dict = yaml.load(f, Loader=yaml.SafeLoader)
    except Exception as e:
        raise Exception('need to set BLUE_SKY_SETTINGS' + str(e))

    return settings_attr_dict(settings_dict)


def configure_worker_app(
    app,
    app_name,
    worker_name=None,
    worker_names=None
):
    if worker_names is None:
        if worker_name is None:
            worker_names = []
        else:
            worker_names = [ worker_name ]

    router = SimpleRouter(app_name)

    app.config_from_object(load_settings_yaml())
    app.conf.task_queue_max_priority = 10
    app.conf.task_queues = router.task_queues(worker_names)
    app.conf.task_routes = (
        router.route_task,
        {
            'workflow_engine.celery.workflow_tasks.run_workflow_node_jobs_by_id':
            {
                'routing_key': 'at_em.#'
            }
        }
    )
