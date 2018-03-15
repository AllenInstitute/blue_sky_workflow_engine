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
import traceback
from django.template import loader
from workflow_engine.models.task import Task
from workflow_engine.models import ONE
from workflow_engine.views import shared, HEADER_PAGES

context = {
    'pages': HEADER_PAGES,
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

# TODO: generalize for any model
def task_json_response(fn):
    def wrapper(request):
        result = {
            'success': True,
            'message': '',
            'payload': {} 
            }

        try:
            if 'task_id'in request.GET:
                task_ids = [ request.GET.get('task_id') ]
            elif 'task_ids' in request.GET:
                task_ids = request.GET.get('task_ids').split(',')

            if task_ids is not None:
                records = Task.objects.filter(id__in=task_ids)
                for task_object in records:
                    fn(task_object, result)
            else:
                result['success'] = False
                result['message'] = 'Missing task_ids'
        except Exception as e:
                result['success'] = False
                result['message'] = str(e) + ' - ' + str(traceback.format_exc())
        except Exception as e:
                result['success'] = False
                result['message'] = str(e) + ' - ' + str(traceback.format_exc())

        return JsonResponse(result)

    return wrapper


@task_json_response
def get_tasks_show_data(task_object, result):
    result['payload'] = shared.order_payload([
        ('id', task_object.id),
        ('job_id', task_object.job_id),
        ('enqueued_object_id', task_object.enqueued_task_object_id),
        ('enqueued_object_class', task_object.enqueued_task_object_class),
        ('enqueued_object', task_object.get_enqueued_object_display()),
        ('run state', task_object.run_state.name),
        ('retry count', str(task_object.retry_count) + '/' + str(task_object.get_max_retries())),
        ('start', task_object.get_start_run_time()),
        ('end', task_object.get_end_run_time()),
        ('file records', ', '.join(task_object.get_file_records())),
        ('created at', task_object.get_created_at()),
        ('updated at', task_object.get_updated_at()),
        ('duration', task_object.get_duration()),
        ('error message', task_object.error_message),
        ('full executable', task_object.full_executable),
        ('log file', task_object.log_file),
        ('input file', task_object.input_file),
        ('output file', task_object.output_file),
        ('pbs id', task_object.pbs_id),
        ('pbs file', task_object.pbs_file)])


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

                #this will be failed if task fails on prep
                if not task.job.has_failed_tasks():
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
