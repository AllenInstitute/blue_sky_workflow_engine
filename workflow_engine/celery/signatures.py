# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2018-2019. Allen Institute. All rights reserved.
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

#
# INGEST TASKS
#
ingest_signature = signature(
    'workflow_engine.celery.ingest_tasks.ingest_task')

#
# CIRCUS TASKS
#
check_circus_status_signature = signature(
    'workflow_engine.check_circus_status')
check_circus_status_signature.set(
    delivery_mode='transient')  # see celery issue 3620
check_circus_task_status_signature = signature(
    'workflow_engine.check_circus_task_status')
check_circus_task_status_signature.set(
    delivery_mode='transient')

#
# MOAB TASKS
#
check_moab_status_signature = signature(
    'workflow_engine.celery.moab_status_tasks.check_moab_status')
check_moab_status_signature.set(
    delivery_mode='transient',
    soft_time_limit=30,
    time_limit=60,
    expires=45)


submit_moab_task_signature = signature(
    'workflow_engine.celery.moab_tasks.submit_moab_task')


submit_worker_task_signature = signature(
    'workflow_engine.celery.local_tasks.submit_worker_task')


kill_moab_task_signature = signature(
    'workflow_engine.celery.moab_tasks.kill_moab_task')


#
# RESULT TASKS
#
process_running_signature = signature(
    'workflow_engine.celery.result_tasks.process_running')


process_finished_execution_signature = signature(
    'workflow_engine.celery.result_tasks.process_finished_execution')


process_failed_execution_signature = signature(
    'workflow_engine.celery.result_tasks.process_failed_execution')


failed_execution_handler_signature = signature(
    'workflow_engine.celery.error_handler.failed_execution_handler')


process_failed_signature = signature(
    'workflow_engine.celery.result_tasks.process_failed')


process_pbs_id_signature = signature(
    'workflow_engine.celery.result_tasks.process_pbs_id')


#
# WORKFLOW / UI TASKS
#
run_workflow_node_jobs_signature = signature(
    'workflow_engine.celery.workflow_tasks.run_workflow_node_jobs_by_id')


# TODO: unimplemented?
run_tasks_signature = signature(
    'workflow_engine.celery.moab_tasks.run_task')


create_job_signature = signature(
    'workflow_engine.celery.workflow_tasks.create_job')


queue_job_signature = signature(
    'workflow_engine.celery.workflow_tasks.queue_job')


enqueue_next_queue_signature = signature(
    'workflow_engine.celery.workflow_tasks.enqueue_next_queue')


kill_job_signature = signature(
    'workflow_engine.celery.workflow_tasks.kill_job')


# MONITOR TASKS
update_dashboard_signature = signature(
    'workflow_engine.broadcast.update_dashboard')
update_dashboard_signature.set(
    delivery_mode='transient',
    soft_time_limit=30,
    time_limit=60,
    expires=45)
