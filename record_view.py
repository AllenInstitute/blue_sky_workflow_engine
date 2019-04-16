# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2017-2018. Allen Institute. All rights reserved.
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
from workflow_engine.models import (
    Executable,
    Job,
    JobQueue,
    Workflow,
    RunState
)
from workflow_engine.views import shared
from workflow_engine.models.task import Task
import simplejson as json
import traceback
from workflow_engine.models.workflow_node import WorkflowNode


def record_json_response(fn):
    def wrapper(request):
        result = {
            'success': True,
            'message': '',
            'payload': {} 
            }

        record_types = {
            'executable': Executable,
            'job_queue': JobQueue,
            'job': Job,
        }

        try:
            record_type = request.GET.get('record_type')

            if record_type is None:
                result['success'] = False
                result['message'] = 'Missing record_type param'
            elif record_type not in record_types.keys():
                result['success'] = False
                result['message'] = 'record_type ' + str(record_type) + ' not supported'
            elif 'record_id'in request.GET:
                record_id = request.GET.get('record_id')
                if record_id == 'new':
                    record_ids = 'new'
                else:
                    record_ids = [ record_id ]
            elif 'record_ids' in request.GET:
                record_ids = request.GET.get('record_ids').split(',')

            if record_ids is not None:
                if 'new' == record_ids:
                    records = [ None ]
                else:
                    records = record_types[record_type].objects.filter(
                        id__in=record_ids)

                try:
                    data = json.loads(request.body.decode('utf-8'))
                except:
                    data = {}

                for record_object in records:
                    fn(record_object, result, record_type, data)
            else:
                result['success'] = False
                result['message'] = 'Missing record_ids'
        except Exception as e:
                result['success'] = False
                result['message'] = str(e) + ' - ' + str(traceback.format_exc())
        except Exception as e:
                result['success'] = False
                result['message'] = str(e) + ' - ' + str(traceback.format_exc())

        return JsonResponse(result)

    return wrapper


@record_json_response
def get_record_info(record, result, record_type, data):
    if record_type == 'executable' and record is None:
        result['payload'] = shared.order_payload([
            ('name', ''),
            ('description', ''),
            ('static_arguments', ''),
            ('executable_path', ''),
            ('pbs_executable_path', ''),
            ('pbs_processor', Executable._meta.get_field('pbs_processor').get_default()),
            ('pbs_queue', Executable._meta.get_field('pbs_queue').get_default()),
            ('pbs_walltime',Executable._meta.get_field('pbs_walltime').get_default())])
    elif record_type == 'executable':
        result['payload'] = shared.order_payload([
            ('name', record.name),
            ('description', record.description),
            ('static_arguments', record.static_arguments),
            ('executable_path', record.executable_path),
            ('pbs_executable_path', record.pbs_executable_path),
            ('pbs_processor', record.pbs_processor),
            ('pbs_queue', record.pbs_queue),
            ('pbs_walltime', record.pbs_walltime)])
    elif record_type == 'job_queue' and record is None:
        result['payload'] = shared.order_payload([
            ('name', ''),
            ('description', ''),
            ('job_strategy_class', ''),
            ('enqueued_object_class', ''),
            ('executable', '')])
    elif record_type == 'job_queue':
        result['payload'] = shared.order_payload([
            ('name', record.name),
            ('description', record.description),
            ('job_strategy_class', record.job_strategy_class),
            ('enqueued_object_class', record.enqueued_object_class),
            ('executable', record.executable.name if record.executable else None)])
    elif record_type == 'job' and record is None:
        result['payload'] = shared.order_payload([
            ('workflow_node_id', ''),
            ('enqueued_object_id', '')])
    elif record_type == 'job':
        result['payload'] = shared.order_payload([
            ('priority', record.priority)])


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
        job.archive()


def check_unique(request):
    result = {}
    success = True
    payload = True
    message = ''

    try:
        record_type = request.GET.get('record_type')
        record_id = request.GET.get('record_id')
        value = request.GET.get('value')
        field_name = request.GET.get('field_name')
        
        if record_type == None:
            success = False
            message = 'Missing record_type param'
        elif record_id == None:
            success = False
            message = 'Missing record_id param'
        elif value == None:
            success = False
            message = 'Missing value param'
        elif field_name == None:
            success = False
            message = 'Missing field_name param'
        elif record_type != 'executable' and \
            record_type != 'job_queue' and \
            record_type != 'workflow_show':
            success = False
            message = 'record_type ' + str(record_type) + ' not supported'
        else:
            if record_type == 'executable':
                if field_name == 'name':
                    executables = Executable.objects.filter(name=value)
                    for executable in executables:
                        if executable.id != int(record_id):
                            payload = False
                else:
                    success = False
                    message = 'record_type ' + str(record_type) + \
                        ' field_name ' + field_name + ' not supported'
            elif record_type == 'job_queue':
                if field_name == 'name':
                    job_queues = JobQueue.objects.filter(name=value)
                    for job_queue in job_queues:
                        if job_queue.id != int(record_id):
                            payload = False
                else:
                    success = False
                    message = 'record_type ' + str(record_type) + \
                        ' field_name ' + field_name + ' not supported'
            elif record_type == 'workflow_show':
                if field_name == 'name':
                    workflows = Workflow.objects.filter(name=value)

                    for workflow in workflows:
                        if workflow.id != int(record_id):
                            payload = False
                else:
                    success = False
                    message = 'record_type ' + str(record_type) + \
                        ' field_name ' + field_name + ' not supported'

    except Exception as e:
            success = False
            message = str(e)
        
    result['success'] = success
    result['message'] = message
    result['payload'] = payload

    return JsonResponse(result)


def get_search_data(request):
    result = {}
    payload = {}
    success = True

    search_type = request.GET.get('search_type')

    if search_type == None:
        success = False
        message = 'missing search_type param'
    else:
        if(search_type == 'executable'):
            executables = Executable.objects.all()
            ids = {}
            names = {}
            pbs_queues = {}
            pbs_processors = {}
            pbs_walltimes = {}

            for executable in executables:
                names[executable.name] = executable.name
                pbs_queues[executable.pbs_queue] = executable.pbs_queue
                ids[executable.id] = executable.id

            payload['ids'] = ids
            payload['names'] = names
            payload['pbs_queues'] = pbs_queues
        elif(search_type == 'job_queue'):
            job_queues = JobQueue.objects.all()
            ids = {}
            names = {}   
            job_strategy_classes = {}
            enqueued_object_classes = {}
            
            for job_queue in job_queues:
                ids[job_queue.id] = job_queue.id
                names[job_queue.name] = job_queue.name
                job_strategy_classes[job_queue.job_strategy_class] = \
                    job_queue.job_strategy_class
                enqueued_object_classes[job_queue.enqueued_object_class] = \
                    job_queue.enqueued_object_class

            payload['ids'] = ids
            payload['names'] = names
            payload['job_strategy_classes'] = job_strategy_classes
            payload['enqueued_object_classes'] = enqueued_object_classes
        elif(search_type == 'job'):
            jobs = Job.objects.all()
            ids = {}
            enqueued_object_ids = {}   
            run_state_ids = {}
            workflow_ids = {}
            
            for job in jobs:
                ids[job.id] = job.id
                enqueued_object_ids[job.enqueued_object_id] = \
                    job.enqueued_object_id

            run_states = RunState.objects.all()
            for run_state in run_states:
                run_state_ids[run_state.id] = run_state.name

            workflows = Workflow.objects.all()
            for workflow in workflows:
                workflow_ids[workflow.id] = workflow.name

            payload['ids'] = ids
            payload['enqueued_object_ids'] = enqueued_object_ids
            payload['run_state_ids'] = run_state_ids
            payload['workflow_ids'] = workflow_ids
        elif(search_type == 'task'):
            tasks = Task.objects.all()
            ids = {}
            enqueued_task_object_ids = {}
            enqueued_task_object_types = {}
            job_ids = {}
            run_state_ids = {}

            for task in tasks:
                ids[task.id] = task.id
                enqueued_task_object_ids[task.enqueued_task_object_id] = \
                    task.enqueued_task_object_id
                enqueued_task_object_types[
                    task.enqueued_task_object_type] = \
                        task.enqueued_task_object_type
                job_ids[task.job.id] = task.job.id

            run_states = RunState.objects.all()
            for run_state in run_states:
                run_state_ids[run_state.id] = run_state.name

            payload['ids'] = ids
            payload['enqueued_task_object_ids'] = enqueued_task_object_ids
            payload['enqueued_task_object_types'] = \
                enqueued_task_object_types
            payload['run_state_ids'] = run_state_ids
            payload['job_ids'] = job_ids
        elif(search_type == 'workflow'):
            workflows = Workflow.objects.all()
            ids = {}
            names = {}
            disabled = {}
            use_pbs = {}

            for workflow in workflows:
                ids[workflow.id] = workflow.id
                names[workflow.name] = workflow.name
                disabled[workflow.disabled] = workflow.disabled
                use_pbs[workflow.use_pbs] = workflow.use_pbs

            payload['workflow_ids'] = ids
            payload['workflow_names'] = names
            payload['disabled'] = disabled
            payload['use_pbs'] = use_pbs

    result['success'] = success
    result['payload'] = payload

    return JsonResponse(result)