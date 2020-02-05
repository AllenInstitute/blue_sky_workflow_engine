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
from django.http import HttpResponse
from django.template import loader
from workflow_engine.mixins import Runnable
from workflow_engine.models import (
    Job,
    WorkflowNode,
    ONE
)
from workflow_engine.views import shared, HEADER_PAGES
from workflow_engine.signatures import (
    queue_job_signature,
    kill_job_signature
)
import logging
from workflow_engine.views.decorators import (
    object_json_response,
    object_json_response2
)


#_TIMEOUT = 20
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
    running_states = request.GET.get('running_state') # To handle when request is coming from workflow page
    enqueued_object_ids = request.GET.get('enqueued_object_ids')
    workflow_ids = request.GET.get('workflow_ids')
    
    if job_ids != None:
        records = Job.objects.filter(id__in=job_ids.split(','), archived=False)
        set_params = True
    else:
        records = Job.objects.filter(archived=False)

    if workflow_node_ids != None:
        records = records.filter(
            workflow_node_id__in=(workflow_node_ids.split(',')))
        set_params = True

    if run_state_ids != None:
        running_states = Runnable.get_run_state_names_by_ids(run_state_ids.split(','))
        records = records.filter(running_state__in=(running_states))
        set_params = True

    if running_states != None:
        records = records.filter(running_state__in=(running_states.split(',')))
        set_params = True

    if enqueued_object_ids != None:
        records = records.filter(enqueued_object_id__in=(enqueued_object_ids.split(',')))
        set_params = True

    if workflow_ids != None:
        worflow_node_ids = {}
        workflow_nodes = WorkflowNode.objects.filter(
            workflow_id__in=workflow_ids.split(','),
            archived=False)
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


@object_json_response2('job_id')
def queue_job(job_id, request, result):
    del request  # not used
    del result  # not used
    queue_job_signature.delay(job_id)
    #outp = r.wait(_TIMEOUT)
    #_log.info('QUEUE_JOB ' + str(outp))


@object_json_response2('job_id')
def kill_job(job_id, request, result):
    del request  # not used
    del result  # not used
    kill_job_signature.delay(job_id[0])
    #outp = r.wait(_TIMEOUT)
    #_log.info('QUEUE_JOB ' + str(outp))


@object_json_response2('job_id')
def run_all_jobs(job_id, request, response):
    del request  # not used
    del response  # not used
    queue_job_signature.delay(job_id)


@object_json_response(id_name='job_id', clazz=Job)
def get_job_status(job_object, request, result):
    del request  # not used
    job_data = {}
    job_data['run_state_name'] = job_object.running_state
    job_data['start_run_time'] = job_object.get_start_run_time()
    job_data['end_run_time'] = job_object.get_end_run_time()
    job_data['duration'] = job_object.get_duration()

    result['payload'][job_object.id] = job_data


@object_json_response(id_name='job_id', clazz=Job)
def get_job_show_data(job_object, request, result):
    del request  # not used
    result['payload'] = shared.order_payload([
        ('id', job_object.id),
        ('enqueued_object_id', job_object.enqueued_object_id),
        ('enqueued_object_class', str(job_object.enqueued_object_type)),
        ('enqueued_object', job_object.get_enqueued_object_display()),
        ('run state', job_object.running_state),
        ('workflow', job_object.workflow_node.workflow.name),
        ('job queue', job_object.workflow_node.job_queue.name),
        ('start', job_object.get_start_run_time()),
        ('end', job_object.get_end_run_time()),
        ('created at', job_object.get_created_at()),
        ('updated at', job_object.get_updated_at()),
        ('duration', job_object.get_duration()),
        ('priority', job_object.priority),
        ('error message', job_object.error_message)])
