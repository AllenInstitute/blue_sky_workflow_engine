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
from django.http import HttpResponse
from django.template import loader
from django.apps import apps
from workflow_engine.views.decorators import object_json_response
from workflow_engine.models.job_queue import JobQueue
from workflow_engine.models import ONE
from workflow_engine.views import shared, HEADER_PAGES


context = {
    'pages': HEADER_PAGES,
}


@object_json_response('job_queue_id', JobQueue)
def get_job_queues_show_data(job_queue_object, request, result):
    result['payload'] = shared.order_payload([
        ('id', job_queue_object.id),
        ('name', job_queue_object.name),
        ('description', job_queue_object.description),
        ('job strategy class', job_queue_object.job_strategy_class),
        ('enqueued object class', job_queue_object.enqueued_object_class),
        ('executable name', job_queue_object.executable.name),  # except ''
        ('executable path', job_queue_object.executable.executable_path),  # except ''
        ('created at', job_queue_object.get_created_at()),
        ('updated at', job_queue_object.get_updated_at())])


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

def get_enqueued_object_classes(request):
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