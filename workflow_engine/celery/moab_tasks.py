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
from workflow_engine.celery import settings
from workflow_client.nb_utils.moab_api import query_and_combine_states,\
    submit_job
from workflow_engine.celery.result_tasks \
    import process_running, process_finished_execution, \
    process_failed_execution
import logging
import django; django.setup()
from celery.canvas import group
import pandas as pd


_log = logging.getLogger('workflow_engine.celery.moab_tasks')


def query_running_task_dict():
    tasks = Task.objects.filter(
        run_state__name__in=['QUEUED', 'RUNNING'])

    task_dict = { t.id: t.run_state.name for t in tasks}

    _log.info(task_dict)

    return task_dict


result_queue = settings.RESULT_MESSAGE_QUEUE_NAME

result_actions = { 
    'running_message':
        lambda x: process_running.s(x).set(queue=result_queue),
    'finished_message':
        lambda x: process_finished_execution.s(x).set(queue=result_queue),
    'failed_message': 
        lambda x: process_failed_execution.s(x).set(queue=result_queue)
}


@celery.shared_task(bind=True, trail=True)
def check_moab_status(self):
    combined_workflow_moab_dataframe = \
        query_and_combine_states(
            query_running_task_dict())

    _log.info('combined_dataframe' + str(combined_workflow_moab_dataframe))

    grp = group(list(pd.concat(
        combined_workflow_moab_dataframe.loc[
            combined_workflow_moab_dataframe[col] == True]['task_id'].apply(fn)
        for (col,fn) in result_actions.items())))

    _log.info(grp)

    grp.apply_async(
        queue=settings.RESULT_MESSAGE_QUEUE_NAME)

    return 'OK'


@celery.shared_task(bind=True, trail=True)
def submit_moab_task(self, task_id):
    try:
        the_task = Task.objects.get(id=task_id)
        if the_task.in_pending_state():
            the_task.set_queued_state()

            return submit_job(
                the_task.id,
                the_task.pbs_file)
        else:
            return None
    except:
        # TODO: need to be able to set the execption message here
        process_failed_execution.apply_async(
            (task_id,),
            queue=settings.RESULT_MESSAGE_QUEUE_NAME)


@celery.shared_task(bind=True, trail=True)
def kill_moab_task(self):
    raise Exception("unimplemented")


# circular imports
from workflow_engine.models.task import Task
