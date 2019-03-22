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
import django; django.setup()
from django.conf import settings
from workflow_client.client_settings import configure_worker_app
from workflow_client.nb_utils.moab_api import (
    query_and_combine_states
)
from workflow_engine.celery.signatures import (
    process_running_signature,
    process_finished_execution_signature,
    process_failed_execution_signature,
    process_failed_signature
)
from celery.exceptions import SoftTimeLimitExceeded
import logging
import celery
from celery.canvas import group
import pandas as pd
import itertools as it


_log = logging.getLogger('workflow_engine.celery.moab_status_tasks')


app = celery.Celery('workflow_engine.celery.moab_status_tasks')
configure_worker_app(app, settings.APP_PACKAGE, 'moab_status')
app.conf.imports = ()


@celery.signals.after_setup_task_logger.connect
def after_setup_celery_task_logger(logger, **kwargs):
    """ This function sets the 'celery.task' logger handler and formatter """
    logging.config.dictConfig(settings.LOGGING)


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
    'running_message': process_running_signature,
    'finished_message': process_finished_execution_signature,
    'failed_execution_message': process_failed_execution_signature,
    'failed_message': process_failed_signature
}

def combined_df_response_group(combined_df):
    return group(
        it.chain.from_iterable(
            combined_df.loc[
                combined_df[col] == True
            ]['task_id'].apply(
                lambda x: sig.clone((x,))
            )
            for (col,sig)
            in result_actions.items()
        )
    )


@celery.shared_task(
    bind=True,
    name='workflow_engine.celery.moab_status_tasks.check_moab_status',
    trail=True)
def check_moab_status(self):
    try:
        combined_workflow_moab_dataframe = query_and_combine_states(
            query_running_task_dicts()
        )

        _log.info('combined_dataframe' + str(combined_workflow_moab_dataframe))

#         grp = group(list(pd.concat(
#             sig.clone((combined_workflow_moab_dataframe.loc[
#                 combined_workflow_moab_dataframe[col] == True]['task_id'],))
#             for (col,sig) in result_actions.items())))
        grp = combined_df_response_group(
            combined_workflow_moab_dataframe
        )

        grp.apply_async(
            broker_connection_timeout=10,
            broker_connection_retry=False,
            queue=settings.RESULT_MESSAGE_QUEUE_NAME,
            on_raw_message=lambda x: _log.info('group result {}', str(x)))
    except SoftTimeLimitExceeded:
        _log.warn('Soft Time Limit Exceeded')
        return 'timeout'

    return 'OK'


# circular imports
from workflow_engine.models import Task
