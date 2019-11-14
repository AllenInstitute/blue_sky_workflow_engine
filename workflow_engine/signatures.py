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
    INGEST = 'workflow_engine.process.workers.ingest_tasks.ingest_task'
    CHECK_CIRCUS_STATUS = 'workflow_engine.check_circus_status'
    CHECK_CIRCUS_TASK_STATUS = 'workflow_engine.check_circus_task_status'
    
    CHECK_MOAB_STATUS = 'workflow_engine.process.workers.moab_status_tasks.check_moab_status'
    SUBMIT_MOAB_TASK = 'workflow_engine.process.workers.moab.moab_tasks.submit_moab_task'
    KILL_MOAB_TASK = 'workflow_engine.process.workers.moab.moab_tasks.kill_moab_task'

    SUBMIT_WORKER_TASK = 'workflow_engine.process.workers.submit_worker_task'

    PROCESS_RUNNING = 'workflow_engine.process.workers.result_tasks.process_running'
    PROCESS_FINISHED_EXECUTION = 'workflow_engine.process.workers.result_tasks.process_finished_execution'
    PROCESS_FAILED_EXECUTION = 'workflow_engine.process.workers.result_tasks.process_failed_execution'
    PROCESS_FAILED = 'workflow_engine.process.workers.result_tasks.process_failed'
    PROCESS_PBS_ID = 'workflow_engine.process.workers.result_tasks.process_pbs_id'

    CREATE_JOB = 'workflow_engine.process.workers.workflow_tasks.create_job'
    QUEUE_JOB = 'workflow_engine.process.workers.workflow_tasks.queue_job'
    RUN_WORKFLOW_NODE_JOBS = 'workflow_engine.process.workers.workflow_tasks.run_workflow_node_jobs_by_id'
    RUN_JOBS_BY_ID = 'workflow_engine.process.workers.workflow_tasks.set_jobs_for_run_by_id'
    ENQUEUE_NEXT = 'workflow_engine.process.workers.workflow_tasks.enqueue_next_queue'
    KILL_JOB = 'workflow_engine.process.workers.workflow_tasks.kill_job'
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
    'workflow_engine.process.workers.moab.moab_tasks.run_task')


create_job_signature = signature(METHODS.CREATE_JOB)
queue_job_signature = signature(METHODS.QUEUE_JOB)
enqueue_next_queue_signature = signature(METHODS.ENQUEUE_NEXT)
kill_job_signature = signature(METHODS.KILL_JOB)


#
# CIRCUS PROCESS WORKER TASKS
#
_PRIORITY_HIGH=6
_PRIORITY_NORMAL=5
_PRIORITY_LOW=4


submit_task_signature = signature(
    'workflow_engine.process.workers.submit_worker_task')
submit_task_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    priority=_PRIORITY_NORMAL,
    retry=False,
    ignore_result=False
)


submit_mock_signature = signature(
    'workflow_engine.process.workers.submit_mock_task')
submit_task_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    priority=_PRIORITY_NORMAL,
    retry=False,
    ignore_result=False,
    expires=60,
)


kill_task_signature = signature(
    'circus_test.kill_task')
kill_task_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    priority=_PRIORITY_HIGH,
    retry=False,
    ignore_result=False
)


task_stdout_signature = signature(
    'circus_test.task_stdout')
task_stdout_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    priority=_PRIORITY_NORMAL,
    retry=False,
    ignore_result=False
)


task_stderr_signature = signature(
    'circus_test.task_stderr')
task_stderr_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    priority=_PRIORITY_NORMAL,
    retry=False,
    ignore_result=False
)


check_status_signature = signature(
    'workflow_engine.check_circus_status')
check_status_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    priority=_PRIORITY_LOW,
    retry=False,
    ignore_result=False
)


check_remote_status_signature = signature(
    'workflow_engine.check_remote_status')
check_status_signature.set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    soft_time_limit=30,
    time_limit=60,
    expires=45,
    priority=_PRIORITY_LOW,
    retry=False,
    ignore_result=False
)


inspect_signature = signature(
    'workflow_engine.inspect_circus').set(
    broker_connection_timeout=10,
    broker_connection_retry=False,
    priority=_PRIORITY_NORMAL,
    retry=False,
    ignore_result=False
)