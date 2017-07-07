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

def jobs(request):
    url = request.get_full_path() + '/1/'

    return jobs_page(request, ONE, url)

def jobs_page(request, page, url=None):

    job_ids = request.GET.get('job_ids')
    sort = request.GET.get('sort')

    if url is None:
        url = request.get_full_path()

    set_params = False

    workflow_node_ids = request.GET.get('workflow_node_ids')
    run_state_ids = request.GET.get('run_state_ids')
    enqueued_object_ids = request.GET.get('enqueued_object_ids')
    workflow_ids = request.GET.get('workflow_ids')
    
    if job_ids != None:
        records = Job.objects.filter(id__in=job_ids.split(','), archived=False)
        set_params = True
    else:
        records = Job.objects.filter(archived=False)

    if workflow_node_ids != None:
        records = records.filter(workflow_node_id__in=(workflow_node_ids.split(',')))
        set_params = True

    if run_state_ids != None:
        records = records.filter(run_state_id__in=(run_state_ids.split(',')))
        set_params = True

    if enqueued_object_ids != None:
        records = records.filter(enqueued_object_id__in=(enqueued_object_ids.split(',')))
        set_params = True

    if workflow_ids != None:
        worflow_node_ids = {}
        workflow_nodes = WorkflowNode.objects.filter(workflow_id__in=workflow_ids.split(','))
        for workflow_node in workflow_nodes:
            worflow_node_ids[workflow_node.id] = True

        records = records.filter(workflow_node_id__in=(list(worflow_node_ids.keys())))
        set_params = True

    if sort == None:
        sort = '-updated_at'

    records = records.order_by(sort)

    add_sort_jobs(context, sort, url, set_params)
    shared.add_context(context, records, url, page, 'jobs')

    template = loader.get_template('jobs.html')
    shared.add_settings_info_to_context(context)
    return HttpResponse(template.render(context, request))

def add_sort_jobs(context, sort, url, set_params):
    context['sort'] = sort
    context['id_sort'] = shared.sort_helper('id', sort, url, set_params)
    context['enqueued_object_id_sort'] = shared.sort_helper('enqueued_object_id', sort, url, set_params)
    context['duration_sort'] = shared.sort_helper('duration', sort, url, set_params)
    context['run_state_id_sort'] = shared.sort_helper('run_state_id', sort, url, set_params)

def queue_job(request):
    result = {}
    success = True
    message = ''

    try:
        job_id = request.GET.get('job_id')
        
        if job_id != None:
            job = Job.objects.get(id=job_id)
            job.set_for_run()
        else:
            success = False
            message = 'Missing job_id'
    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['message'] = message

    return JsonResponse(result)

def kill_job(request):
    result = {}
    success = True
    message = ''

    try:
        job_id = request.GET.get('job_id')
        
        if job_id != None:
            job = Job.objects.get(id=job_id)
            job.set_process_killed_state()
            job.kill_tasks()
            job.set_end_run_time()
        else:
            success = False
            message = 'Missing job_id'
    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['message'] = message

    return JsonResponse(result)

def get_job_status(request):
    result = {}
    success = True
    message = ''
    payload = {}

    try:
        job_ids = request.GET.get('job_ids')
    
        if job_ids != None:
            records = Job.objects.filter(id__in=job_ids.split(','))

            for record in records:
                job_data = {}
                job_data['run_state_name'] = record.run_state.name
                job_data['start_run_time'] = record.get_start_run_time()
                job_data['end_run_time'] = record.get_end_run_time()
                job_data['duration'] = record.get_duration()

                payload[record.id] = job_data
        else:
            success = False
            message = 'Missing job_ids'
    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['message'] = message
    result['payload'] = payload

    return JsonResponse(result)

def get_job_show_data(request):
    result = {}
    success = True
    payload = {}
    message = ''

    try:
        job_id = request.GET.get('job_id')
        
        if job_id != None:
            job = Job.objects.get(id=job_id)

            order = shared.set_order(payload, ZERO, 'id', job.id)
            order = shared.set_order(payload, order, 'enqueued_object_id', job.enqueued_object_id)
            order = shared.set_order(payload, order, 'enqueued_object_class', job.get_enqueued_object_class_type())
            order = shared.set_order(payload, order, 'enqueued_object', job.get_enqueued_object_display())
            order = shared.set_order(payload, order, 'run state', job.run_state.name)
            order = shared.set_order(payload, order, 'workflow', job.workflow_node.workflow.name)
            order = shared.set_order(payload, order, 'job queue', job.workflow_node.job_queue.name)
            order = shared.set_order(payload, order, 'start', job.get_start_run_time())
            order = shared.set_order(payload, order, 'end', job.get_end_run_time())
            order = shared.set_order(payload, order, 'created at', job.get_created_at())
            order = shared.set_order(payload, order, 'updated at', job.get_updated_at())
            order = shared.set_order(payload, order, 'duration', job.get_duration())
            order = shared.set_order(payload, order, 'priority', job.priority)
            order = shared.set_order(payload, order, 'error message', job.error_message)

            payload['order_length'] = order
        else:
            success = False
            message = 'Missing job_id'
    except Exception as e:
            success = False
            message = str(e)
        
    result['success'] = success
    result['message'] = message
    result['payload'] = payload

    return JsonResponse(result)

def run_all_jobs(request):
    result = {}
    success = True
    message = ''

    try:
        job_ids = request.GET.get('job_ids')
    
        if job_ids != None:
            records = Job.objects.filter(id__in=job_ids.split(','))

            for record in records:
                record.set_for_run_if_valid()
        else:
            success = False
            message = 'Missing job_ids'
    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['message'] = message

    return JsonResponse(result)