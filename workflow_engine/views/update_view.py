# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2017. Allen Institute. All rights reserved.
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
from workflow_engine.views import shared
from workflow_engine.models.executable import Executable
from workflow_engine.models.job_queue import JobQueue
from workflow_engine.models.workflow_node import WorkflowNode
from workflow_engine.models.job import Job
from workflow_engine.models.run_state import RunState
from workflow_engine.views.record_info_view \
    import record_json_response


@record_json_response
def update_record(record, result, record_type, data):
    if record_type == 'executable' and record is None:
        record = Executable()
    elif record_type == 'executable':
        # TODO: replace w/ workflow config
        record.name = data['name']
        record.description = data['description']
        record.static_arguments = shared.to_none(data['static_arguments'])
        record.executable_path = data['executable_path']
        record.pbs_executable_path = data['pbs_executable_path']
        record.pbs_processor = data['pbs_processor']
        record.pbs_queue = data['pbs_queue']
        record.pbs_walltime = data['pbs_walltime']
    elif record_type == 'job_queue' and record is None:
        record = JobQueue()
    elif record_type == 'job_queue':
        record.name = data['name']
        record.description = shared.to_none(data['description'])
        record.job_strategy_class = data['job_strategy_class']
        record.enqueued_object_class = data['enqueued_object_class']

        if(data['executable']):
            record.executable = Executable.objects.get(name=data['executable'])
        else:
            record.executable = None
    elif record_type == 'job' and record is None:
        workflow_node = WorkflowNode.objects.get(id=data['workflow_node_id'])

        record = Job()
        record.workflow_node = workflow_node
        record.enqueued_object_id = data['enqueued_object_id']
        record.run_state = RunState.get_pending_state()
        record.priority = workflow_node.priority
        record.archived = False
    else:
        priority = data['priority']
        record.priority = priority

    record.save()