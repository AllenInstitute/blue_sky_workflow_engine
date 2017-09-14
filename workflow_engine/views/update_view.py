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
from django.http import JsonResponse
from workflow_engine.models import *
from workflow_engine.views import shared
import json

def update_record(request):
    result = {}
    success = True
    message = ''

    try:
        record_type = request.GET.get('record_type')
        record_id = request.GET.get('record_id')

        if record_type == None:
            success = False
            message = 'Missing record_type param'
        elif record_type != 'executable' and record_type != 'job_queue' and record_type != 'job':
            success = False
            message = 'record_type ' + str(record_type) + ' not supported'
        else:
            data = json.loads(request.body.decode('utf-8'))

            if record_type == 'executable':

                if record_id == 'new':
                    executable = Executable()
                else:
                    executable = Executable.objects.get(id=record_id)

                executable.name = data['name']
                executable.description = data['description']
                executable.static_arguments = shared.to_none(data['static_arguments'])
                executable.executable_path = data['executable_path']
                executable.pbs_executable_path = data['pbs_executable_path']
                executable.pbs_processor = data['pbs_processor']
                executable.pbs_queue = data['pbs_queue']
                executable.pbs_walltime = data['pbs_walltime']
                executable.save()
            elif record_type == 'job_queue':
                if record_id == 'new':
                    job_queue = JobQueue()
                else:
                    job_queue = JobQueue.objects.get(id=record_id)

                job_queue.name = data['name']
                job_queue.description = shared.to_none(data['description'])
                job_queue.job_strategy_class = data['job_strategy_class']
                job_queue.enqueued_object_class = data['enqueued_object_class']

                if(data['executable']):
                    job_queue.executable = Executable.objects.get(name=data['executable'])
                else:
                    job_queue.executable = None

                job_queue.save()
            elif record_type == 'job':
                if record_id == 'new':
                    workflow_node = WorkflowNode.objects.get(id=data['workflow_node_id'])

                    job = Job()
                    job.workflow_node = workflow_node
                    job.enqueued_object_id = data['enqueued_object_id']
                    job.run_state = RunState.get_pending_state()
                    job.priority = workflow_node.priority
                    job.archived = False
                    job.save()
                else:
                    priority = data['priority']
                    job = Job.objects.get(id=record_id)
                    job.priority = priority
                    job.save()
                
    except Exception as e:
            success = False
            message = str(e)  
        
    result['success'] = success
    result['message'] = message

    return JsonResponse(result)