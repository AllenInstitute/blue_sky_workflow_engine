from django.http import JsonResponse
from django.http import HttpResponse
import traceback
from django.template import loader
from django.apps import apps
from workflow_engine.models import *
from workflow_engine.views import shared
import json

pages = ['index', 'jobs', 'workflows', 'workflow_creator', 'job_queues', 'executables']
context = {
    'pages': pages,
}

def get_job_queues_show_data(request):
    result = {}
    success = True
    payload = {}
    message = ''

    try:
        job_queue_id = request.GET.get('job_queue_id')
        
        if job_queue_id != None:
            job_queue = JobQueue.objects.get(id=job_queue_id)

            order = shared.set_order(payload, ZERO, 'id', job_queue.id)
            order = shared.set_order(payload, order, 'name', job_queue.name)
            order = shared.set_order(payload, order, 'description', job_queue.description)
            order = shared.set_order(payload, order, 'job strategy class', job_queue.job_strategy_class)
            order = shared.set_order(payload, order, 'enqueued object class', job_queue.enqueued_object_class)

            try:
                order = shared.set_order(payload, order, 'executable name', job_queue.executable.name)
            except:
                order = shared.set_order(payload, order, 'executable name', '')

            try:
                order = shared.set_order(payload, order, 'executable path', job_queue.executable.executable_path)
            except:
                order = shared.set_order(payload, order, 'executable path', '')

            order = shared.set_order(payload, order, 'created at', job_queue.get_created_at())
            order = shared.set_order(payload, order, 'cpdated at', job_queue.get_updated_at())

            payload['order_length'] = order

        else:
            success = False
            message = 'Missing job_queue_id'
    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['message'] = message
    result['payload'] = payload

    return JsonResponse(result)

def job_queues(request):
    url = request.get_full_path() + '/1/'

    return job_queues_page(request, ONE, url)

def add_sort_job_queues(context, sort, url, set_params):
    context['sort'] = sort
    context['id_sort'] = shared.sort_helper('id', sort, url, set_params)
    context['name_sort'] = shared.sort_helper('name', sort, url, set_params)
    context['description_sort'] = shared.sort_helper('description', sort, url, set_params)
    context['job_strategy_class_sort'] = shared.sort_helper('job_strategy_class', sort, url, set_params)
    context['enqueued_object_class_sort'] = shared.sort_helper('enqueued_object_class', sort, url, set_params)
    context['executable_sort'] = shared.sort_helper('executable', sort, url, set_params)
    context['created_at_sort'] = shared.sort_helper('created_at', sort, url, set_params)
    context['updated_at_sort'] = shared.sort_helper('updated_at', sort, url, set_params)

def job_queues_page(request, page, url = None):
    job_queue_ids = request.GET.get('job_queue_ids')
    job_queue_names = request.GET.get('job_queue_names')
    job_strategy_classes = request.GET.get('job_strategy_classes')
    enqueued_object_classes = request.GET.get('enqueued_object_classes')
    sort = request.GET.get('sort')

    if url is None:
        url = request.get_full_path()

    set_params = False
    
    if job_queue_ids != None:
        records = JobQueue.objects.filter(id__in=job_queue_ids.split(','))
        set_params = True
    elif job_queue_names != None:
        records = JobQueue.objects.filter(name__in=job_queue_names.split(','))
        set_params = True
    else:
        records = JobQueue.objects.all()

    if job_strategy_classes != None:
        records = records.filter(job_strategy_class__in=(job_strategy_classes.split(',')))
        set_params = True

    if enqueued_object_classes != None:
        records = records.filter(enqueued_object_class__in=(enqueued_object_classes.split(',')))
        set_params = True

    if sort == None:
        sort = '-updated_at'
        
    records = records.order_by(sort)

    add_sort_job_queues(context, sort, url, set_params)
    shared.add_context(context, records, url, page, 'job_queues')

    template = loader.get_template('job_queues.html')
    shared.add_settings_info_to_context(context)
    return HttpResponse(template.render(context, request))

def get_enqueued_object_classses(request):
    result = {}
    success = True
    payload = []
    message = ''

    try:
        app_models = apps.get_app_config('development').get_models()
        
        for model in app_models:
            payload.append(model.__name__)

        payload.sort()  

    except Exception as e:
            success = False
            message = str(e)
        
    result['success'] = success
    result['message'] = message
    result['payload'] = payload

    return JsonResponse(result)