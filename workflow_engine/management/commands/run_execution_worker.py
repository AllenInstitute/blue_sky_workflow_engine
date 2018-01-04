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
import pika
from workflow_engine.models.run_state import RunState
from workflow_engine.models.task import Task
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import logging
import traceback

def callback(ch, method, properties, body):
    Command.cb(ch, method, properties, body)


class Command(BaseCommand):
    _log = logging.getLogger(
        'workflow_engine.mananagement.commands.run_execution_worker')
    help = 'response handler for the message queue'
    STATE = 0
    TASK_ID = 1
    PBS_ID = 2


    # TODO: change this to use workflow_client.ingest_client
    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)
        logging.getLogger('run_execution_worker').setLevel(logging.INFO)

        credentials = pika.PlainCredentials(settings.MESSAGE_QUEUE_USER,
                                            settings.MESSAGE_QUEUE_PASSWORD)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                settings.MESSAGE_QUEUE_HOST,
                settings.MESSAGE_QUEUE_PORT,
                '/',
                credentials))

        MQ = settings.CELERY_MESSAGE_QUEUE_NAME
        Command._log.info("listening to queue: %s" % (MQ))
        channel = connection.channel()
        channel.queue_declare(queue=MQ,
                              durable=True)
        channel.basic_consume(callback,
                              queue=MQ,
                              no_ack=True)
        Command._log.info(
            ' [*] Waiting for messages. To exit press CTRL+C')

        channel.start_consuming()

    @classmethod
    def process_running(cls, task, strategy):
        strategy.running_task(task)

    @classmethod
    def process_finished_execution(cls, task, strategy):
        strategy.finish_task(task)

    @classmethod
    def process_failed_execution(cls, task, strategy):
        strategy.fail_execution_task(task)

    @classmethod
    def cb(cls, ch, method, properties, body):
        body = body.decode("utf-8") 
        Command._log.info(" [x] Received " + str(body))

        try:
            body_data = body.split(',')
            state = body_data[Command.STATE]
            task_id = body_data[Command.TASK_ID]

            task = Task.objects.get(id=task_id)

            strategy = task.get_strategy()
            if state == RunState.get_running_state().name:
                Command.process_running(task, strategy)
            elif state == RunState.get_finished_execution_state().name:
                Command.process_finished_execution(task, strategy)
            elif state == RunState.get_failed_execution_state().name:
                Command.process_failed_execution(task, strategy)
            elif state == 'PBS_ID':
                task.pbs_id = str(body_data[Command.PBS_ID])
                task.save()

        except Exception as e:
            Command._log.error(
                'Something went wrong: ' + (traceback.print_exc(e)))


