from django.http import JsonResponse
from django.http import HttpResponse
import traceback
from django.template import loader
from workflow_engine.models import *
from workflow_engine.views import shared
import json

pages = ['index', 'jobs', 'workflows', 'workflow_creator', 'job_queues', 'executables']
context = {
    'pages': pages,
}

def tasks_page(request, page, url = None):
    job_id = request.GET.get('job_id')
    task_ids = request.GET.get('task_ids')
    sort = request.GET.get('sort')

    enqueued_task_object_ids = request.GET.get('enqueued_task_object_ids')
    enqueued_task_object_classes = request.GET.get('enqueued_task_object_classes')
    job_ids = request.GET.get('job_ids')
    run_state_ids = request.GET.get('run_state_ids')

    if url is None:
        url = request.get_full_path()

    set_params = False

    if job_id != None:
        records = Task.objects.filter(job_id=job_id, archived=False)
        set_params = True
    elif task_ids != None:
        records = Task.objects.filter(id__in=task_ids.split(','), archived=False)
        set_params = True
    else:
        records = Task.objects.filter(archived=False)
        set_params = True

    if enqueued_task_object_ids != None:
        records = records.filter(enqueued_task_object_id__in=(enqueued_task_object_ids.split(',')))

    if enqueued_task_object_classes != None:
        records = records.filter(enqueued_task_object_class__in=(enqueued_task_object_classes.split(',')))

    if job_ids != None:
        records = records.filter(job_id__in=(job_ids.split(',')))

    if run_state_ids != None:
        records = records.filter(run_state_id__in=(run_state_ids.split(',')))

    if sort == None:
        sort = '-updated_at'
    
    records = records.order_by(sort)

    context['job_id'] = job_id

    add_sort_tasks(context, sort, url, set_params)
    shared.add_context(context, records, url, page, 'tasks')
 
    template = loader.get_template('tasks.html')
    shared.add_settings_info_to_context(context)
    return HttpResponse(template.render(context, request))


def tasks(request):
    url = request.get_full_path() + '/1/'

    return tasks_page(request, ONE, url)

def add_sort_tasks(context, sort, url, set_params):
    context['sort'] = sort
    context['id_sort'] = shared.sort_helper('id', sort, url, set_params)
    context['enqueued_task_object_id_sort'] = shared.sort_helper('enqueued_task_object_id', sort, url, set_params)
    context['retry_count_sort'] = shared.sort_helper('retry_count', sort, url, set_params)
    context['duration_sort'] = shared.sort_helper('duration', sort, url, set_params)
    context['start_run_time_sort'] = shared.sort_helper('start_run_time', sort, url, set_params)
    context['end_run_time_sort'] = shared.sort_helper('end_run_time', sort, url, set_params)
    context['run_state_sort'] = shared.sort_helper('run_state', sort, url, set_params)

def get_tasks_show_data(request):
    result = {}
    success = True
    payload = {}
    message = ''

    try:
        task_id = request.GET.get('task_id')
        
        if task_id != None:
            task = Task.objects.get(id=task_id)

            order = shared.set_order(payload, ZERO, 'id', task.id)
            order = shared.set_order(payload, order, 'job_id', task.job_id)
            order = shared.set_order(payload, order, 'enqueued_object_id', task.enqueued_task_object_id)
            order = shared.set_order(payload, order, 'enqueued_object_class', task.enqueued_task_object_class)
            order = shared.set_order(payload, order, 'enqueued_object', task.get_enqueued_object_display())
            order = shared.set_order(payload, order, 'run state', task.run_state.name)
            order = shared.set_order(payload, order, 'retry count', str(task.retry_count) + '/' + str(task.get_max_retries()))
            order = shared.set_order(payload, order, 'start', task.get_start_run_time())
            order = shared.set_order(payload, order, 'end', task.get_end_run_time())
            order = shared.set_order(payload, order, 'file records', ', '.join(task.get_file_records()))
            order = shared.set_order(payload, order, 'created at', task.get_created_at())
            order = shared.set_order(payload, order, 'updated at', task.get_updated_at())
            order = shared.set_order(payload, order, 'duration', task.get_duration())
            order = shared.set_order(payload, order, 'error message', task.error_message)
            order = shared.set_order(payload, order, 'full executable', task.full_executable)
            order = shared.set_order(payload, order, 'log file', task.log_file)
            order = shared.set_order(payload, order, 'input file', task.input_file)
            order = shared.set_order(payload, order, 'output file', task.output_file)
            order = shared.set_order(payload, order, 'pbs id', task.pbs_id)
            order = shared.set_order(payload, order, 'pbs file', task.pbs_file)

            payload['order_length'] = order
        else:
            success = False
            message = 'Missing task_id'
    except Exception as e:
            success = False
            message = str(e)
        
    result['success'] = success
    result['message'] = message
    result['payload'] = payload

    return JsonResponse(result)

def queue_task(request):
    result = {}
    success = True
    message = ''

    try:
        task_id = request.GET.get('task_id')
        
        if task_id != None:
            task = Task.objects.get(id=task_id)
            task.run_task()
            if task.job.can_rerun:
                task.reset_retry_count()
                task.job.set_pending_state()
        else:
            success = False
            message = 'Missing task_id'
    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['message'] = message

    return JsonResponse(result)

def kill_task(request):
    result = {}
    success = True
    message = ''

    try:
        task_id = request.GET.get('task_id')
        
        if task_id != None:
            task = Task.objects.get(id=task_id)
            task.set_process_killed_state()
            task.kill_task()
        else:
            success = False
            message = 'Missing task_id'
    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['message'] = message

    return JsonResponse(result)

def get_task_status(request):
    result = {}
    success = True
    message = ''
    payload = {}

    try:
        task_ids = request.GET.get('task_ids')
    
        if task_ids != None:
            records = Task.objects.filter(id__in=task_ids.split(','))

            for record in records:
                task_data = {}
                task_data['run_state_name'] = record.run_state.name
                task_data['start_run_time'] = record.get_start_run_time()
                task_data['end_run_time'] = record.get_end_run_time()
                task_data['duration'] = record.get_duration()

                payload[record.id] = task_data
        else:
            success = False
            message = 'Missing task_ids'
    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['message'] = message
    result['payload'] = payload

    return JsonResponse(result)

def download_bash(request):
    result = {}
    success = True
    message = ''
    payload = []
    error_message = []

    try:
        task_ids = request.GET.get('task_ids')
    
        if task_ids != None:
            records = Task.objects.filter(id__in=task_ids.split(','))

            for record in records:

                try:
                    strategy = record.get_strategy()
                    if strategy.is_execution_strategy():
                        full_executable = strategy.get_full_executable(record)
                        payload.append(full_executable)
                except Exception as e:
                    error_message.append(str(e))
        else:
            success = False
            message = 'Missing task_ids'
    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['message'] = message
    result['payload'] = payload
    result['error_message'] = error_message

    return JsonResponse(result)
