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
from django.http import HttpResponse
import traceback
from django.template import loader
from workflow_engine.models.job import Job
from workflow_engine.models.workflow_node import WorkflowNode
from workflow_engine.models import ONE
from workflow_engine.views import shared, HEADER_PAGES
import workflow_client.worker_client as worker_client
import logging

_log = logging.getLogger('workflow_engine.views.job_view')

context = {
    'pages': HEADER_PAGES,
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

def job_json_response(fn):
    def wrapper(request):
        result = {
            'success': True,
            'message': '',
            'payload': {} 
            }

        try:
            if 'job_id'in request.GET:
                job_ids = [ request.GET.get('job_id') ]
            elif 'job_ids' in request.GET:
                job_ids = request.GET.get('job_ids').split(',')

            if job_ids is not None:
                records = Job.objects.filter(id__in=job_ids)
                for job_object in records:
                    fn(job_object, result)
            else:
                result['success'] = False
                result['message'] = 'Missing job_ids'
        except Exception as e:
                result['success'] = False
                result['message'] = str(e) + ' - ' + str(traceback.format_exc())
        except Exception as e:
                result['success'] = False
                result['message'] = str(e) + ' - ' + str(traceback.format_exc())

        return JsonResponse(result)

    return wrapper

# TODO: generalize for any model
def job_json_response2(fn):
    def wrapper(request):
        result = {
            'success': True,
            'message': '',
            'payload': {} 
            }

        try:
            if 'job_id'in request.GET:
                job_ids = [ request.GET.get('job_id') ]
            elif 'job_ids' in request.GET:
                job_ids = request.GET.get('job_ids').split(',')
            else:
                job_ids = None

            if job_ids is not None:
                fn(job_ids, result)
            else:
                result['success'] = False
                result['message'] = 'Missing job_ids'

            _log.info(result)
        except Exception as e:
                result['success'] = False
                mess = str(e) + ' - ' + str(traceback.format_exc())
                _log.error(mess)
                result['message'] = mess
        except Exception as e:
                result['success'] = False
                mess = str(e) + ' - ' + str(traceback.format_exc())
                _log.error(mess)
                result['message'] = mess

        return JsonResponse(result)

    return wrapper


@job_json_response2
def queue_job(job_id, result):
    r = worker_client.queue_job.apply_async(
        (job_id),
        queue='workflow')
    outp = r.get()
    _log.info('QUEUE_JOB ' + str(outp))
    #WorkflowController.set_job_for_run(job_object)


@job_json_response2
def kill_job(job_id, result):
    r = worker_client.kill_job.apply_async(
        (job_id),
        queue='workflow')
    outp = r.get()
    _log.info('QUEUE_JOB ' + str(outp))
    #Job.kill_job(job_id)
    # job_object.kill()


@job_json_response2
def run_all_jobs(job_id, response):
    worker_client.queue_job.apply_async(
        (job_id),
        queue='workflow')
    #WorkflowController.set_job_for_run_if_valid(job_id)


@job_json_response
def get_job_status(job_object, result):
    job_data = {}
    job_data['run_state_name'] = job_object.run_state.name
    job_data['start_run_time'] = job_object.get_start_run_time()
    job_data['end_run_time'] = job_object.get_end_run_time()
    job_data['duration'] = job_object.get_duration()

    result['payload'][job_object.id] = job_data


@job_json_response
def get_job_show_data(job_object, result):
    result['payload'] = shared.order_payload([
        ('id', job_object.id),
        ('enqueued_object_id', job_object.enqueued_object_id),
        ('enqueued_object_class', job_object.get_enqueued_object_class_type()),
        ('enqueued_object', job_object.get_enqueued_object_display()),
        ('run state', job_object.run_state.name),
        ('workflow', job_object.workflow_node.workflow.name),
        ('job queue', job_object.workflow_node.job_queue.name),
        ('start', job_object.get_start_run_time()),
        ('end', job_object.get_end_run_time()),
        ('created at', job_object.get_created_at()),
        ('updated at', job_object.get_updated_at()),
        ('duration', job_object.get_duration()),
        ('priority', job_object.priority),
        ('error message', job_object.error_message)])
