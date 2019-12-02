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
from workflow_engine.process.workers.moab_api import (
    query_and_combine_states,
    submit_job,
    delete_moab_task
)
from django.core.exceptions import ObjectDoesNotExist
import logging
from celery.canvas import group
import pandas as pd
from workflow_engine.signatures import (
    process_running_signature,
    process_finished_execution_signature,
    process_failed_execution_signature,
    process_failed_signature,
    process_pbs_id_signature
)


_log = logging.getLogger('workflow_engine.celery.pbs_tasks')


def query_running_task_dicts():
    tasks = Task.objects.filter(
        running_state__in=['QUEUED', 'RUNNING'])

    task_dicts = [{
        'task_id': t.id,
        'workflow_state': t.running_state,
        'moab_id': t.pbs_id } for t in tasks if t.pbs_task()]

    _log.info('task dicts: ' + str(task_dicts))

    return task_dicts



# Todo need to use moab id and task id in all cases
result_actions = { 
    'running_message':
        lambda x: process_running_signature(x),
    'finished_message':
        lambda x: process_finished_execution_signature(x),
    'failed_execution_message': 
        lambda x: process_failed_execution_signature(x),
    'failed_message':
        lambda x: process_failed_signature(x)
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

    grp.delay()

    return 'OK'

@celery.shared_task(bind=True, trail=True)
def submit_moab_task(self, task_id):
    _log.info('Submitting task %d', task_id)

    try:
        the_task = Task.objects.get(id=task_id)
 
        pbs_file = the_task.get_strategy().get_pbs_file(the_task)
        the_task.create_pbs_file(pbs_file)

        if the_task.in_pending_state():
            _log.info('in pending state')

            moab_id = submit_job(
                the_task.id,
                the_task.pbs_file)

            if moab_id != 'ERROR':
                the_task.set_queued_state(moab_id)
                process_pbs_id_signature.delay(
                    task_id, moab_id)
            else:
                process_failed_execution_signature.delay(
                    task_id, fail_now=True)

        _log.info("MOAB ID: {}".format(moab_id))
    except Exception as e:
        moab_id = None
        msg = 'Error submitting task {}'.format(str(e))
        _log.error(msg)
        process_failed_execution_signature.delay(
            task_id, fail_now=True)


# TODO: change name to something like process task state
# Not sure if we still need name
# Do need a UI task like this
@celery.shared_task(bind=True)
def run_task(self, name, args):
    raise Exception("Removed/Unimplemented")


@celery.shared_task(bind=True, trail=True)
def kill_moab_task(self, task_id):
    try:
        the_task = Task.objects.get(id=task_id)
        delete_moab_task(the_task.pbs_id)
    except ObjectDoesNotExist as e:
        _log.warning("Cannot kill task %s, does not exist. %s",
                     task_id,
                     str(e))

# circular imports
from workflow_engine.models import Task
