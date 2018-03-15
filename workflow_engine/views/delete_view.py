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
from workflow_engine.models import ZERO
from workflow_engine.views.record_info_view \
    import record_json_response


@record_json_response
def delete_record(record, result, record_type, data):
    result['link_content'] = ''
    result['link'] = ''

    if record_type == 'executable':
        executable = record
        job_queues = executable.get_job_queues()

        if len(job_queues) > ZERO:
            result['success'] = False

            job_queue_message = []
            ids = []
            for job_queue in job_queues:
                job_queue_message.append(str(job_queue.name))
                ids.append(str(job_queue.id))

            result['message'] = 'At least one job queue is using this executable. Please delete for following job queue(s) before delete: '
            result['link_content'] = ','.join(job_queue_message)
            result['link'] = '/workflow_engine/job_queues?job_queue_ids=' + ','.join(ids)
        else:
            executable.delete()
    elif record_type == 'job_queue':
        job_queue = record
    
        workflow_nodes = job_queue.get_workflow_nodes()

        # TODO: make this a workflow_controller method
        workflows = {}
        for workflow_node in workflow_nodes:
            workflow = workflow_node.workflow
            workflows[workflow.id] = workflow

        if len(workflows) > ZERO:
            result['success'] = False

            workflow_message = []
            ids = []
            for workflow_id in workflows.keys():
                workflow_message.append(
                    str(workflows[workflow_id].name))
                ids.append(str(workflow_id))

            result['message'] = 'At least one workflow is using this job_queue. Please delete for following workflow(s) before delete: '
            result['link_content'] = ','.join(workflow_message)
            result['link'] = '/workflow_engine/workflows?workflow_ids=' + ','.join(ids)
        else:
            job_queue.delete()
    elif record_type == 'job':
        job = record
        job.archive_record()
