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
import os
import simplejson as json
from workflow_client.ingest_consumer import IngestConsumer
from workflow_engine.models import RunState, Task, Workflow
from workflow_engine.models.import_class import import_class
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import logging
import traceback


def callback(ch, method, properties, body):
    Command.cb(ch, method, properties, body)

class Command(BaseCommand):
    help = 'ingest handler for the message queues'
    _log = logging.getLogger(
        'workflow_engine.management.commands.ingest')
    _default_callback = callback
    _callback = _default_callback

    def set_callback(callback_fn):
        Command._callback = callback_fn

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)
        logging.getLogger(
            'development.management.commands.ingest_reference_set').setLevel(
                logging.INFO)

        with IngestConsumer(
            settings.MESSAGE_QUEUE_HOST,
            settings.MESSAGE_QUEUE_PORT,
            settings.MESSAGE_QUEUE_USER,
            settings.MESSAGE_QUEUE_PASSWORD,
            '', settings.INGEST_MESSAGE_QUEUE_NAME) as c:
            c.consume(callback)


    @classmethod
    def cb(cls, ch, method, properties, body):
        body = body.decode("utf-8") 
        Command._log.info(" [x] Received " + str(body))

        try:
            body_data = json.loads(body)
            Command._log.info(body_data)
            ingester = import_class(settings.INGEST_STRATEGY)
            workflow, enqueued_object = \
                ingester.create_enqueued_object(body_data)
            Workflow.start_workflow(workflow,
                                    enqueued_object)
        except Exception as e:
            Command._log.error(
                'Something went wrong: ' + traceback.print_exc(e))

