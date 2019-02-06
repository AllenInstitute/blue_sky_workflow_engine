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
import celery
from django.conf import settings
from workflow_client.nb_utils.moab_api import (
    query_and_combine_states
)
import logging
from celery.canvas import group
import pandas as pd
from workflow_engine.celery.result_tasks import (
    process_running,
    process_finished_execution,
    process_failed_execution,
    process_failed
)


_log = logging.getLogger('workflow_engine.celery.moab_status_tasks')


def query_running_task_dicts():
    tasks = Task.objects.filter(
        run_state__name__in=['QUEUED', 'RUNNING'])

    task_dicts = [{
        'task_id': t.id,
        'workflow_state': t.run_state.name,  # TODO: run_state
        'moab_id': t.pbs_id } for t in tasks if t.pbs_task()]

    _log.info('task dicts: ' + str(task_dicts))

    return task_dicts


result_queue = settings.RESULT_MESSAGE_QUEUE_NAME

# Todo need to use moab id and task id in all cases
result_actions = { 
    'running_message':
        lambda x: process_running.s(x).set(
            queue=result_queue),
    'finished_message':
        lambda x: process_finished_execution.s(x).set(
            queue=result_queue),
    'failed_execution_message': 
        lambda x: process_failed_execution.s(x).set(
            queue=result_queue),
    'failed_message':
        lambda x: process_failed.s(x).set(
            queue=result_queue)
}


@celery.shared_task(bind=True, trail=True)
def check_moab_status(self):
    combined_workflow_moab_dataframe = \
        query_and_combine_states(
            query_running_task_dicts())

    _log.info('combined_dataframe' + str(combined_workflow_moab_dataframe))

    grp = group(list(pd.concat(
        combined_workflow_moab_dataframe.loc[
            combined_workflow_moab_dataframe[col] == True]['task_id'].apply(fn)
        for (col,fn) in result_actions.items())))

    grp.apply_async(
        broker_connection_timeout=10,
        broker_connection_retry=False,
        queue=settings.RESULT_MESSAGE_QUEUE_NAME,
        on_raw_message=lambda x: _log.info('group result {}', str(x)))

    # _log.info('Result group:' + json.dumps(grp, indent=2))

    return 'OK'


# circular imports
from workflow_engine.models import Task
