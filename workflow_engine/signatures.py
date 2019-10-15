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

_DEFAULT_TIME_LIMIT = 60

class METHODS:
    '''Explicitly used in the name parameter of celery.shared task
       and in the celery signatures to decouple the task name from
       the module it is defined in and to allow small client processes
       to import signatures without needing to import the task module
       and all dependencies.
    '''
    INGEST = 'workflow_engine.celery.ingest_tasks.ingest_task'
    CHECK_CIRCUS_STATUS = 'workflow_engine.check_circus_status'
    CHECK_CIRCUS_TASK_STATUS = 'workflow_engine.check_circus_task_status'
    
    CHECK_MOAB_STATUS = 'workflow_engine.celery.moab_status_tasks.check_moab_status'
    SUBMIT_MOAB_TASK = 'workflow_engine.celery.moab_tasks.submit_moab_task'
    KILL_MOAB_TASK = 'workflow_engine.celery.moab_tasks.kill_moab_task'

    SUBMIT_WORKER_TASK = 'workflow_engine.celery.submit_worker_task'

    PROCESS_RUNNING = 'workflow_engine.celery.result_tasks.process_running'
    PROCESS_FINISHED_EXECUTION = 'workflow_engine.celery.result_tasks.process_finished_execution'
    PROCESS_FAILED_EXECUTION = 'workflow_engine.celery.result_tasks.process_failed_execution'
    PROCESS_FAILED = 'workflow_engine.celery.result_tasks.process_failed'
    PROCESS_PBS_ID = 'workflow_engine.celery.result_tasks.process_pbs_id'

    CREATE_JOB = 'workflow_engine.celery.workflow_tasks.create_job'
    QUEUE_JOB = 'workflow_engine.celery.workflow_tasks.queue_job'
    RUN_WORKFLOW_NODE_JOBS = 'workflow_engine.celery.workflow_tasks.run_workflow_node_jobs_by_id'
    RUN_JOBS_BY_ID = 'workflow_engine.celery.workflow_tasks.set_jobs_for_run_by_id'
    ENQUEUE_NEXT = 'workflow_engine.celery.workflow_tasks.enqueue_next_queue'
    KILL_JOB = 'workflow_engine.celery.workflow_tasks.kill_job'

    UPDATE_DASHBOARD = 'workflow_engine.broadcast.update_dashboard'
#
# INGEST TASKS
#
ingest_signature = signature(METHODS.INGEST)

#
# CIRCUS TASKS
#
check_circus_status_signature = signature(METHODS.CHECK_CIRCUS_STATUS)
check_circus_status_signature.set(
    delivery_mode='transient')  # see celery issue 3620


check_circus_task_status_signature = signature(METHODS.CHECK_CIRCUS_TASK_STATUS)
check_circus_task_status_signature.set(
    delivery_mode='transient')

#
# MOAB TASKS
#
check_moab_status_signature = signature(METHODS.CHECK_MOAB_STATUS)
check_moab_status_signature.set(
    delivery_mode='transient',
    soft_time_limit=30,
    time_limit=_DEFAULT_TIME_LIMIT,
    expires=45)
submit_moab_task_signature = signature(METHODS.SUBMIT_MOAB_TASK)
submit_moab_task_signature.set(
    time_limit=60
)
kill_moab_task_signature = signature(METHODS.KILL_MOAB_TASK)
kill_moab_task_signature.set(
    time_limit=_DEFAULT_TIME_LIMIT
)


submit_worker_task_signature = signature(METHODS.SUBMIT_WORKER_TASK)
submit_worker_task_signature.set(
    time_limit=_DEFAULT_TIME_LIMIT
)

#
# RESULT TASKS
#
process_running_signature = signature(METHODS.PROCESS_RUNNING)
# process_running_signature.set(
#     time_limit=_DEFAULT_TIME_LIMIT
# )
process_finished_execution_signature = signature(METHODS.PROCESS_FINISHED_EXECUTION)
process_finished_execution_signature.set(
    time_limit=_DEFAULT_TIME_LIMIT
)
process_failed_execution_signature = signature(METHODS.PROCESS_FAILED_EXECUTION)
process_failed_execution_signature.set(
    time_limit=_DEFAULT_TIME_LIMIT
)
process_failed_signature = signature(METHODS.PROCESS_FAILED)
process_failed_signature.set(
    time_limit=_DEFAULT_TIME_LIMIT
)
process_pbs_id_signature = signature(METHODS.PROCESS_PBS_ID)
process_pbs_id_signature.set(
    time_limit=_DEFAULT_TIME_LIMIT
)


#
# WORKFLOW / UI TASKS
#
run_workflow_node_jobs_signature = signature(METHODS.RUN_WORKFLOW_NODE_JOBS)
run_jobs_by_id_signature = signature(METHODS.RUN_JOBS_BY_ID)


# TODO: unimplemented?
run_tasks_signature = signature(
    'workflow_engine.celery.moab_tasks.run_task')


create_job_signature = signature(METHODS.CREATE_JOB)
queue_job_signature = signature(METHODS.QUEUE_JOB)
enqueue_next_queue_signature = signature(METHODS.ENQUEUE_NEXT)
kill_job_signature = signature(METHODS.KILL_JOB)


# MONITOR TASKS
update_dashboard_signature = signature(METHODS.UPDATE_DASHBOARD)
update_dashboard_signature.set(
    delivery_mode='transient',
    soft_time_limit=30,
    time_limit=60,
    expires=45)
