# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2019. Allen Institute. All rights reserved.
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
from workflow_client import signatures
from celery.canvas import group
import itertools as it
import pandas as pd
import logging

class TaskStatus(object):
    _log = logging.getLogger('workflow_engine.celery.task_status')
    
    RESULT_ACTIONS = { 
        'running_message': signatures.process_running_signature,
        'finished_message': signatures.process_finished_execution_signature,
        'failed_execution_message': signatures.process_failed_execution_signature,
        'failed_message': signatures.process_failed_signature
    }
    
    def __init__(self, remote_queues):
        self.remote_queues=remote_queues

    def workflow_state_dataframe(self, state_dict):
        """
        state_dict: { id: "<state>" }
        """
        workflow_state_df = pd.DataFrame(
            state_dict,
            columns=['task_id', 'workflow_state', 'remote_id'])

        TaskStatus._log.info('workflow_state_df size: {}'.format(
            len(workflow_state_df.index))
        )

        workflow_state_df['task_name'] = workflow_state_df['task_id'].map(
            'task_{}'.format
        )

        return workflow_state_df

    def combined_df(self, blue_sky_job_df, remote_job_df):
        combined_df = blue_sky_job_df.merge(
            remote_job_df,
            on=('remote_id','task_name'),
            how='left'
        )

        combined_df['remote_state'].fillna('Unknown', inplace=True)
        combined_df['running_message'] = False
        combined_df['finished_message'] = False
        combined_df['failed_message'] = False
        combined_df['failed_execution_message'] = False

        combined_df.loc[
            combined_df.workflow_state.isin(["QUEUED"]) &
            combined_df.remote_state.isin(["Running"]),
            'running_message'] = True

        combined_df.loc[
            combined_df.workflow_state.isin(["QUEUED","RUNNING"]) &
            combined_df.remote_state.isin(["Completed"]) &
            (combined_df.exit_code == 0),
            'finished_message'] = True

        combined_df.loc[
            combined_df.workflow_state.isin(["QUEUED","RUNNING"]) &
            combined_df.remote_state.isin(["Completed"]) &
            (combined_df.exit_code != 0),
            'failed_message'] = True

        combined_df.loc[
            combined_df.workflow_state.isin(["QUEUED","RUNNING"]) &
            combined_df.remote_state.isin(
                ["Expired", "Removed", "Vacated", "Unknown"]),
            'failed_execution_message'] = True

        return combined_df

    def combined_df_response_group(self, combined_df):
        return group(
            it.chain.from_iterable(
                combined_df.loc[
                    combined_df[col] == True
                ]['task_id'].apply(
                    lambda x: sig.clone((x,))
                )
                for (col,sig)
                in TaskStatus.RESULT_ACTIONS.items()
            )
        )

    def send_response_message_group(self, combined_df):
        self.combined_df_response_group(
            combined_df
        ).delay()

    def send_remote_status_results(self, running_task_dicts):
        remote_job_df = self.query_remote_state(running_task_dicts)

        blue_sky_job_df = self.workflow_state_dataframe(
            running_task_dicts
        )
        combined_df = self.combined_df(blue_sky_job_df, remote_job_df)
        TaskStatus._log.info("Combined dataframe size: {}".format(
            len(combined_df.index))
        )
        self.send_response_message_group(combined_df)
