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
from django.core.exceptions import ObjectDoesNotExist
from workflow_engine.views import shared
from workflow_engine.models import *

def delete_record(request):
    result = {}
    success = True
    message = ''
    link_content = ''
    link = ''

    try:
        record_type = request.GET.get('record_type')
        record_id = request.GET.get('record_id')
        
        if record_type == None:
            success = False
            message = 'Missing record_type param'

        elif record_id == None:
            success = False
            message = 'Missing record_id param'

        elif record_type != 'executable' and record_type != 'job_queue' and record_type != 'job':
            success = False
            message = 'record_type ' + str(record_type) + ' in not supported'
        else:
            if record_type == 'executable':
                executable = Executable.objects.get(id=record_id)
                job_queues = executable.get_job_queues()

                if len(job_queues) > ZERO:
                    success = False

                    job_queue_message = []
                    ids = []
                    for job_queue in job_queues:
                        job_queue_message.append(str(job_queue.name))
                        ids.append(str(job_queue.id))

                    message = 'At least one job queue is using this executable. Please delete for following job queue(s) before delete: '
                    link_content = ','.join(job_queue_message)
                    link = '/workflow_engine/job_queues?job_queue_ids=' + ','.join(ids)
                else:
                    executable.delete()
            elif record_type == 'job_queue':
                job_queue = JobQueue.objects.get(id=record_id)
            
                workflow_nodes = job_queue.get_workflow_nodes()

                workflows = {}
                for workflow_node in workflow_nodes:
                    workflow = workflow_node.workflow
                    workflows[workflow.id] = workflow

                if len(workflows) > ZERO:
                    success = False

                    workflow_message = []
                    ids = []
                    for workflow_id in workflows.keys():
                        workflow_message.append(str(workflows[workflow_id].name))
                        ids.append(str(workflow_id))

                    message = 'At least one workflow is using this job_queue. Please delete for following workflow(s) before delete: '
                    link_content = ','.join(workflow_message)
                    link = '/workflow_engine/workflows?workflow_ids=' + ','.join(ids)

                else:
                    job_queue.delete()

            elif record_type == 'job':
                job = Job.objects.get(id=record_id)
                job.archive_record()


    except ObjectDoesNotExist as e:
        success = False
        message = 'Could not find a ' + str(record_type) + ' record with id of ' + str(record_id) 

    except Exception as e:
            success = False
            message = str(e)
        
    result['success'] = success
    result['message'] = message
    result['link_content'] = link_content
    result['link'] = link


    return JsonResponse(result)