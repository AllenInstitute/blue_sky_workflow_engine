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
from .task_status import TaskStatus
from workflow_client.tasks.circus_signatures import (
    check_status_signature,
)
import pandas as pd


class CircusStatus(TaskStatus):
    STATUS_MAP = {
        0: 'Running',
        1: 'Completed'
    }

    def __init__(self, remote_queues=None):
        if remote_queues is None:
            remote_queues = ['circus']

        super(CircusStatus, self).__init__(remote_queues)


    def query_remote_state(self, status_dict):
        """
        state_dicts: [{ 'remote_id': 'Moab.123'}, ... ]
        """
        #circus_inspect = inspect_signature.delay().get() # TODO: asynchronous
        status_dict = check_status_signature()# TODO: asynchronous

        circus_state_df = pd.DataFrame.from_records((
            (k,
             job['wid'],
             CircusStatus.STATUS_MAP.get(job['status'], 'Unknown'),
             job['username'],
             (job['exit_code']
                  if job['exit_code'] is not None
                  else -1
             )) for k,job in status_dict.items()),
            columns=[
                'remote_id', 'task_name', 'remote_state', 'user', 'exit_code']
        )

        return circus_state_df

