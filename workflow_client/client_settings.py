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
from kombu import Exchange, Queue, binding
from kombu.common import Broadcast
from django.conf import settings
from workflow_client.simple_router import SimpleRouter
import os
import yaml
import logging


_log = logging.getLogger('workflow_client.client_settings')


class settings_attr_dict(dict):
    __getattr__ = dict.get


def load_settings_yaml():
    settings_dict = {}

    try: 
        blue_sky_settings_json = \
            os.environ.get('BLUE_SKY_SETTINGS',
                           'blue_sky_settings.yml')

        with open(blue_sky_settings_json) as f:
            settings_dict = settings_attr_dict(yaml.load(f))
    except Exception as e:
        raise Exception('need to set BLUE_SKY_SETTINGS' + str(e))

    return settings_dict


def get_message_broker_url(celery_settings):
    return 'pyamqp://%s:%s@%s:%s//' % (
        celery_settings.MESSAGE_QUEUE_USER,
        celery_settings.MESSAGE_QUEUE_PASSWORD,
        celery_settings.MESSAGE_QUEUE_HOST,
        celery_settings.MESSAGE_QUEUE_PORT)


def configure_worker_app(app, app_name, worker_name=None):
    celery_settings = load_settings_yaml()
    router = SimpleRouter(app_name)

    app.config_from_object(config_object(
        celery_settings))
    app.conf.task_queues = router.task_queues(worker_name)
    app.conf.task_routes = (router.route_task,)


def config_object(s):
    return settings_attr_dict({
        'broker_url': get_message_broker_url(s),
        'result_backend': 'rpc://',
        'task_serializer': 'json',
        'result_serializer': 'json',
        'accept_content': ['json'],
        'timezone': 'US/Pacific',
        'enable_utc': True,
        #'task_queues': [ 'ingest' ],
        'task_default_queue': s.DEFAULT_MESSAGE_QUEUE_NAME
    })

# settings = load_settings_yaml()
