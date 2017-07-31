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