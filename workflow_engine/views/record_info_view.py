from django.http import JsonResponse
from workflow_engine.models import *
from workflow_engine.views import shared

def get_record_info(request):
    result = {}
    success = True
    payload = {}
    message = ''

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
            message = 'record_type ' + str(record_type) + ' not supported'
        else:
            if record_type == 'executable':
                if record_id == 'new':
                    order = shared.set_order(payload, ZERO, 'name', '')
                    order = shared.set_order(payload, order, 'description', '')
                    order = shared.set_order(payload, order, 'static_arguments', '')
                    order = shared.set_order(payload, order, 'executable_path', '')
                    order = shared.set_order(payload, order, 'pbs_processor', Executable._meta.get_field('pbs_processor').get_default())
                    order = shared.set_order(payload, order, 'pbs_queue', Executable._meta.get_field('pbs_queue').get_default())
                    order = shared.set_order(payload, order, 'pbs_walltime', Executable._meta.get_field('pbs_walltime').get_default())
                else:
                    executable = Executable.objects.get(id=record_id)
                    order = shared.set_order(payload, ZERO, 'name', executable.name)
                    order = shared.set_order(payload, order, 'description', executable.description)
                    order = shared.set_order(payload, order, 'static_arguments', executable.static_arguments)
                    order = shared.set_order(payload, order, 'executable_path', executable.executable_path)
                    order = shared.set_order(payload, order, 'pbs_processor', executable.pbs_processor)
                    order = shared.set_order(payload, order, 'pbs_queue', executable.pbs_queue)
                    order = shared.set_order(payload, order, 'pbs_walltime', executable.pbs_walltime)
            elif record_type == 'job_queue':
                if record_id == 'new':
                    order = shared.set_order(payload, ZERO, 'name', '')
                    order = shared.set_order(payload, order, 'description', '')
                    order = shared.set_order(payload, order, 'job_strategy_class', '')
                    order = shared.set_order(payload, order, 'enqueued_object_class', '')
                    order = shared.set_order(payload, order, 'executable', '')
                else:
                    job_queue = JobQueue.objects.get(id=record_id)
                    order = shared.set_order(payload, ZERO, 'name', job_queue.name)
                    order = shared.set_order(payload, order, 'description', job_queue.description)
                    order = shared.set_order(payload, order, 'job_strategy_class', job_queue.job_strategy_class)
                    order = shared.set_order(payload, order, 'enqueued_object_class', job_queue.enqueued_object_class)
                    if job_queue.executable:
                        order = shared.set_order(payload, order, 'executable', job_queue.executable.name)
                    else:
                        order = shared.set_order(payload, order, 'executable', None)
                    
            elif record_type == 'job':
                if record_id == 'new':
                    order = shared.set_order(payload, ZERO, 'workflow_node_id', '')
                    order = shared.set_order(payload, order, 'enqueued_object_id', '')       
                else:
                    job = Job.objects.get(id=record_id)
                    order = shared.set_order(payload, ZERO, 'priority', job.priority)
            payload['order_length'] = order

    except ObjectDoesNotExist as e:
        success = False
        message = 'Could not find a ' + str(record_type) + ' record with id of ' + str(record_id) 

    except Exception as e:
            success = False
            message = str(e)
        
    result['success'] = success
    result['message'] = message
    result['payload'] = payload

    return JsonResponse(result)

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
        elif record_type != 'executable' and record_type != 'job_queue' and record_type != 'workflow_show':
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
                    message = 'record_type ' + str(record_type) +  ' field_name ' + field_name + ' not supported'
            elif record_type == 'job_queue':
                if field_name == 'name':
                    job_queues = JobQueue.objects.filter(name=value)
                    for job_queue in job_queues:
                        if job_queue.id != int(record_id):
                            payload = False
                else:
                    success = False
                    message = 'record_type ' + str(record_type) +  ' field_name ' + field_name + ' not supported'
            elif record_type == 'workflow_show':
                if field_name == 'name':
                    workflows = Workflow.objects.filter(name=value)

                    for workflow in workflows:
                        if workflow.id != int(record_id):
                            payload = False
                else:
                    success = False
                    message = 'record_type ' + str(record_type) +  ' field_name ' + field_name + ' not supported'              

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
                pbs_processors[executable.pbs_processor] = executable.pbs_processor
                pbs_walltimes[executable.pbs_walltime] = executable.pbs_walltime

            payload['ids'] = ids
            payload['names'] = names
            payload['pbs_queues'] = pbs_queues
            payload['pbs_processors'] = pbs_processors
            payload['pbs_walltimes'] = pbs_walltimes
        elif(search_type == 'job_queue'):
            job_queues = JobQueue.objects.all()
            ids = {}
            names = {}   
            job_strategy_classes = {}
            enqueued_object_classes = {}
            
            for job_queue in job_queues:
                ids[job_queue.id] = job_queue.id
                names[job_queue.name] = job_queue.name
                job_strategy_classes[job_queue.job_strategy_class] = job_queue.job_strategy_class
                enqueued_object_classes[job_queue.enqueued_object_class] = job_queue.enqueued_object_class

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
                enqueued_object_ids[job.enqueued_object_id] = job.enqueued_object_id

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
            enqueued_task_object_classes = {}   
            job_ids = {}
            run_state_ids = {}

            for task in tasks:
                ids[task.id] = task.id
                enqueued_task_object_ids[task.enqueued_task_object_id] = task.enqueued_task_object_id
                enqueued_task_object_classes[task.enqueued_task_object_class] = task.enqueued_task_object_class
                job_ids[task.job.id] = task.job.id

            run_states = RunState.objects.all()
            for run_state in run_states:
                run_state_ids[run_state.id] = run_state.name

            payload['ids'] = ids
            payload['enqueued_task_object_ids'] = enqueued_task_object_ids
            payload['enqueued_task_object_classes'] = enqueued_task_object_classes
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

            # print('payload: ' + str(payload))

    result['success'] = success
    result['payload'] = payload

    return JsonResponse(result)