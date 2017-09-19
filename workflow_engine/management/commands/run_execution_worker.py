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
from workflow_engine.models import RunState, Task
from django.conf import settings

STATE = 0
TASK_ID = 1
PBS_ID = 2

credentials = pika.PlainCredentials(settings.MESSAGE_QUEUE_USER, settings.MESSAGE_QUEUE_PASSWORD)
connection = pika.BlockingConnection(pika.ConnectionParameters(settings.MESSAGE_QUEUE_HOST, settings.MESSAGE_QUEUE_PORT,'/', credentials))

channel = connection.channel()
channel.queue_declare(queue=settings.MESSAGE_QUEUE_NAME)

def process_running(task, strategy):
    strategy.running_task(task)

def process_finished_execution(task, strategy):
    strategy.finish_task(task)

def process_failed_execution(task, strategy):
    strategy.fail_execution_task(task)

def callback(ch, method, properties, body):
    body = body.decode("utf-8") 
    print(" [x] Received " + str(body))

    try:
        body_data = body.split(',')
        state = body_data[STATE]
        task_id = body_data[TASK_ID]

        task = Task.objects.get(id=task_id)

        strategy = task.get_strategy()
        if state == RunState.get_running_state().name:
            process_running(task, strategy)
        elif state == RunState.get_finished_execution_state().name:
            process_finished_execution(task, strategy)
        elif state == RunState.get_failed_execution_state().name:
            process_failed_execution(task, strategy)
        elif state == 'PBS_ID':
            task.pbs_id = str(body_data[PBS_ID])
            task.save()

    except Exception as e:
        print('Something went wrong: ' + str(e))

channel.basic_consume(callback,queue=settings.MESSAGE_QUEUE_NAME,no_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()