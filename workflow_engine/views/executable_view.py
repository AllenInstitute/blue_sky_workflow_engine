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

def executables_page(request, page, url=None):
    executable_ids = request.GET.get('executable_ids')
    names = request.GET.get('names')
    pbs_queues = request.GET.get('pbs_queues')
    pbs_processors = request.GET.get('pbs_processors')
    pbs_walltimes = request.GET.get('pbs_walltimes')

    sort = request.GET.get('sort')

    if url is None:
        url = request.get_full_path()

    set_params = False

    if executable_ids != None:
        records = Executable.objects.filter(id__in=executable_ids.split(','))
        set_params = True
    else:
        records = Executable.objects.all()

    if names != None:
        records = records.filter(name__in=(names.split(',')))
        set_params = True

    if pbs_queues != None:
        records = records.filter(pbs_queue__in=(pbs_queues.split(',')))
        set_params = True

    if pbs_processors != None:
        records = records.filter(pbs_processor__in=(pbs_processors.split(',')))
        set_params = True

    if pbs_walltimes != None:
        records = records.filter(pbs_walltime__in=(pbs_walltimes.split(',')))
        set_params = True

    if sort == None:
        sort = '-updated_at'
    
    records = records.order_by(sort)

    add_sort_executable(context, sort, url, set_params)
    shared.add_context(context, records, url, page, 'executables')

    template = loader.get_template('executables.html')
    shared.add_settings_info_to_context(context)
    return HttpResponse(template.render(context, request))

def executables(request):
    url = request.get_full_path() + '/1/'

    return executables_page(request, ONE, url)

def get_executable_names(request):
    result = {}
    success = True
    payload = []
    message = ''

    try:
        executables = Executable.objects.all().order_by('name')
        for executable in executables:
            payload.append(executable.name)

    except Exception as e:
            success = False
            message = str(e)
        
    result['success'] = success
    result['message'] = message
    result['payload'] = payload

    return JsonResponse(result)

def add_sort_executable(context, sort, url, set_params):
    context['sort'] = sort
    context['id_sort'] = shared.sort_helper('id', sort, url, set_params)
    context['name_sort'] = shared.sort_helper('name', sort, url, set_params)
    context['description_sort'] = shared.sort_helper('description', sort, url, set_params)
    context['executable_path_sort'] = shared.sort_helper('executable_path', sort, url, set_params)
    context['static_arguments_sort'] = shared.sort_helper('static_arguments', sort, url, set_params)
    context['pbs_processor_sort'] = shared.sort_helper('pbs_processor', sort, url, set_params)
    context['pbs_walltime_sort'] = shared.sort_helper('pbs_walltime', sort, url, set_params)
    context['pbs_queue_sort'] = shared.sort_helper('pbs_queue', sort, url, set_params)
    context['created_at_sort'] = shared.sort_helper('created_at', sort, url, set_params)
    context['updated_at_sort'] = shared.sort_helper('updated_at', sort, url, set_params)