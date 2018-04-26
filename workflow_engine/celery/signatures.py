# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2018. Allen Institute. All rights reserved.
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
from celery import signature
from django.conf import settings


#_EXCHANGE = settings.APP_PACKAGE
#
# INGEST TASKS
#
ingest_signature = signature(
    'workflow_engine.celery.ingest_tasks.ingest_task')
ingest_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    # exchange=_EXCHANGE,
    routing_key='ingest',
    queue=settings.INGEST_MESSAGE_QUEUE_NAME)


#
# MOAB TASKS
#
check_moab_status_signature = signature(
    'workflow_engine.celery.moab_tasks.check_moab_status')
check_moab_status_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    delivery_mode='transient',  # see celery issue 3620
    # exchange=_EXCHANGE,
    routing_key='moab',
    queue=settings.MOAB_MESSAGE_QUEUE_NAME)


submit_moab_task_signature = signature(
    'workflow_engine.celery.moab_tasks.submit_moab_task')
submit_moab_task_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    # exchange=_EXCHANGE,
    routing_key='moab',
    queue=settings.MOAB_MESSAGE_QUEUE_NAME)


kill_moab_task_signature = signature(
    'workflow_engine.celery.moab_tasks.kill_moab_task')
kill_moab_task_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    # exchange=_EXCHANGE,
    routing_key='moab',
    queue=settings.MOAB_MESSAGE_QUEUE_NAME)


#
# RESULT TASKS
#
process_running_signature = signature(
    'workflow_engine.celery.result_tasks.process_running')
process_running_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    # exchange=_EXCHANGE,
    routing_key='result',
    queue=settings.RESULT_MESSAGE_QUEUE_NAME,
    debug=True)


process_finished_execution_signature = signature(
    'workflow_engine.celery.result_tasks.process_finished_execution')
process_finished_execution_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    # exchange=_EXCHANGE,
    routing_key='result',
    queue=settings.RESULT_MESSAGE_QUEUE_NAME)


process_failed_execution_signature = signature(
    'workflow_engine.celery.result_tasks.process_failed_execution')
process_failed_execution_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    # exchange=_EXCHANGE,
    routing_key='result',
    queue=settings.RESULT_MESSAGE_QUEUE_NAME)


process_pbs_id_signature = signature(
    'workflow_engine.celery.result_tasks.process_pbs_id')
process_pbs_id_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    # exchange=_EXCHANGE,
    routing_key='result',
    queue=settings.RESULT_MESSAGE_QUEUE_NAME)


#
# WORKFLOW / UI TASKS
#
run_workflow_node_jobs_signature = signature(
    'workflow_engine.celery.run_tasks.run_workflow_node_jobs_by_id')
run_workflow_node_jobs_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    # exchange=_EXCHANGE,
    routing_key='workflow',
    queue=settings.WORKFLOW_MESSAGE_QUEUE_NAME)


# TODO: unimplemented?
run_tasks_signature = signature(
    'workflow_engine.celery.run_tasks.run_task')
run_tasks_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    # exchange=_EXCHANGE,
    routing_key='moab',
    queue=settings.MOAB_MESSAGE_QUEUE_NAME)


create_job_signature = signature(
    'workflow_engine.celery.worker_tasks.create_job')
create_job_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    # exchange=_EXCHANGE,
    routing_key='workflow',
    queue=settings.WORKFLOW_MESSAGE_QUEUE_NAME)


queue_job_signature = signature(
    'workflow_engine.celery.worker_tasks.queue_job')
queue_job_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    # exchange=_EXCHANGE,
    routing_key='workflow',
    queue=settings.WORKFLOW_MESSAGE_QUEUE_NAME)


run_normal_signature = signature(
    'workflow_engine.celery.worker_tasks.run_normal')
run_normal_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    # exchange=_EXCHANGE,
    routing_key='workflow',
    queue=settings.WORKFLOW_MESSAGE_QUEUE_NAME)


kill_job_signature = signature(
    'workflow_engine.celery.worker_tasks.kill_job')
kill_job_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    # exchange=_EXCHANGE,
    routing_key='workflow',
    queue=settings.WORKFLOW_MESSAGE_QUEUE_NAME)


cancel_task_signature = signature(
    'workflow_engine.celery.worker_tasks.cancel_task')
cancel_task_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    # exchange=_EXCHANGE,
    routing_key='workflow',
    queue=settings.WORKFLOW_MESSAGE_QUEUE_NAME)
