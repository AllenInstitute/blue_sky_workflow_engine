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
from workflow_engine.models import ZERO
from workflow_engine.models.workflow import Workflow
from workflow_engine.models.workflow_node import WorkflowNode
from workflow_engine.models.run_state import RunState
from workflow_engine.import_class import import_class
from workflow_engine.views   import shared, HEADER_PAGES
from workflow_engine.workflow_controller import WorkflowController
from workflow_engine.models.executable import Executable
from collections import deque
from workflow_engine.celery.signatures \
    import run_workflow_node_jobs_signature, create_job_signature
from workflow_engine.views.decorators \
    import object_json_response, object_json_response2, object_json_all_response,\
    object_yaml_all_response
import logging
import json


_log = logging.getLogger('workflow_engine.views.workflow_view')
context = {
    'pages': HEADER_PAGES,
}

def workflows(request):
    context['selected_page'] = 'workflows'
    template = loader.get_template('workflows.html')
    shared.add_settings_info_to_context(context)

    workflow_ids = request.GET.get('workflow_ids')
    workflow_names = request.GET.get('workflow_names')
    search_disabled = request.GET.get('search_disabled')
    search_use_pbs = request.GET.get('search_use_pbs')
    
    if workflow_ids != None:
        workflows = Workflow.objects.filter(
            id__in=workflow_ids.split(','),
            archived=False)
    elif workflow_names != None:
        workflows = Workflow.objects.filter(
            name__in=workflow_names.split(','),
            archived=False)
    else:
        workflows = Workflow.objects.filter(archived=False)

    if search_disabled != None:
        workflows = workflows.filter(
            disabled=shared.string_to_bool(search_disabled),
            archived=False)

    if search_use_pbs != None:
        workflows = workflows.filter(
            use_pbs=shared.string_to_bool(search_use_pbs),
            archived=False)

    workflows = workflows.order_by('-name')

    workflow_setups = []

    workflows_data = []
    for workflow in workflows:
        _log.info(
            'viewing workflow %s. disabled: %s' % (workflow.name,
                                                   str(workflow.disabled)))
        disabled_class = ''
        if workflow.disabled:
            disabled_class = 'disabled_workflow'

        workflow_setups.append({'name': workflow.name, 'id':workflow.id, 'use_pbs':workflow.use_pbs, 'disabled_class': disabled_class})

        head_workflow_nodes = workflow.get_head_workflow_nodes()
        _log.info('found %d head nodes' % (len(head_workflow_nodes)))

        for node in head_workflow_nodes:
            _log.info('head node: %s' % (str(node)))
            workflow_info = {}
            workflow_info['chart'] = build_chart(workflow)
            workflow_info['nodeStructure'] = build_node_structure(node)
            workflows_data.append(workflow_info)

    context['workflows'] = json.dumps(workflows_data)
    context['workflow_setups'] = workflow_setups
    context['number_of_records'] = len(workflow_setups)

    return HttpResponse(template.render(context, request))

def child_connector():
    style = {'arrow-end' : 'classic', 'stroke': '#bbb'}
    return {'style': style, 'type':'bCurve'} 


def get_node_color_class(run_state, prev_run_state):
    if prev_run_state == 'failed_state':
        node_color_class = prev_run_state
    elif RunState.is_failed_type_state(run_state):
        node_color_class = 'failed_state'
    elif RunState.is_running_type_state(run_state):
        node_color_class = 'running_state'
    else:
        node_color_class = 'success_state'

    return node_color_class


@object_json_response('workflow_node_id', WorkflowNode)
def get_workflow_status(node, request, result):
    job_states = node.get_job_states()
    node_color_class = get_node_color_class(None, None)

    for name in job_states.keys():
        node_color_class = get_node_color_class(name, node_color_class)

    node_data = {}
    node_data['name'] = node.get_node_name()
    node_data['node_color_class'] = node_color_class

    result['payload'][node.id] = node_data


def get_node_content(node):
    job_states = node.get_job_states()

    node_color_class = get_node_color_class(None, None)

    for name in job_states.keys():
        node_color_class = get_node_color_class(name, node_color_class)

    disabled_class = ''
    if node.disabled:
        disabled_class = ' disabled_node'

    html = '<div id="node_' + str(node.id) + '" class="workflow_node ' + node_color_class + disabled_class + '" node_id="'+ str(node.id) + '" workflow_id="' + str(node.workflow.id) + '">'
    html += '<p class="workflow_node_header">' + node.get_node_name() + '</p>'
    html += '</div>'

    return html

def build_chart(workflow):
    chart = {}
    chart['container'] = '#workflow_' + str(workflow.id)
    chart['rootOrientation'] = 'WEST'
    chart['connectors'] = {'type': 'step', 'style': {'stroke-width': 2}}
    chart['nodeAlign'] = 'BOTTOM'
    chart['levelSeparation'] = 100

    return chart

def build_workflow_children(node):
    result = {}

    result['innerHTML'] = get_node_content(node)
    result['connectors'] = child_connector()

    child_nodes = node.get_children()

    children = []
    for child_node in child_nodes:
        children.append(build_workflow_children(child_node))

    if len(children) > ZERO:
        result['children'] = children

    return result

def build_node_structure(node):
    node_structure = {}
    node_structure['innerHTML'] = get_node_content(node)
    node_structure['connectors'] = child_connector()

    child_nodes = node.get_children()

    children = []
    for child_node in child_nodes:
        children.append(build_workflow_children(child_node))

    node_structure['children'] = children

    return node_structure


@object_json_response('workflow_id', Workflow)
def get_head_workflow_node_id(workflow_object, request, result):
    result['payload'] = workflow_object.get_head_workflow_nodes().first().id


@object_json_response('workflow_node_id', WorkflowNode)
def get_enqueued_objects(workflow_node, request, result):
    record_names = []
    record_ids = {}

    enqueued_object_class = workflow_node.job_queue.enqueued_object_class
    _log.debug('Workflow node job queue enqueued class name: %s' % (
        (enqueued_object_class)))

    enqueued_object_class_instance = \
        import_class(enqueued_object_class)
    _log.debug('Workflow node job queue enqueued class: %s' % (
        str(enqueued_object_class)))

    for record in enqueued_object_class_instance.objects.all():
        record_names.append(str(record))
        record_ids[str(record)] = record.id

    record_names.sort()

    result['record_names'] = record_names
    result['record_ids'] = record_ids
    result['priority'] = workflow_node.priority
    result['enqueued_object_class'] = enqueued_object_class.split('.')[-1]


@object_json_response('workflow_node_id', WorkflowNode)
def run_jobs(workflow_node, request, result):
    n = workflow_node.job_queue.name
    result['message'] = n
    WorkflowController.set_jobs_for_run(n)


@object_json_response2('workflow_node_id')
def create_job(workflow_node_ids, request, result):
    workflow_node_id = workflow_node_ids[0]
    priority = request.GET.get('priority')
    enqueued_object_id = request.GET.get('enqueued_object_id')

    if priority == None:
        result['success'] = False
        result['message'] = 'missing priority param'
    elif enqueued_object_id == None:
        result['success'] = False
        result['message'] = 'missing enqueued_object_id param'
    else:
        # TODO: get some kind of resonse here
        create_job_signature.delay(
            workflow_node_id,
            enqueued_object_id,
            priority)


@object_json_response('workflow_node_id', WorkflowNode)
def get_node_info(workflow_node, request, result):
    payload = result['payload']

    payload['job_queue'] = workflow_node.job_queue.name
    payload['job_queue_link'] = \
        'job_queues?job_queue_ids=' + \
        str(workflow_node.job_queue.id)
    try:
        payload['executable'] = workflow_node.job_queue.executable.name
        payload['executable_link'] = \
            'executables?executable_ids=' + \
            str(workflow_node.job_queue.executable.id)
    except:
        payload['executable'] = ''
        payload['executable_link'] = ''
    
    payload['enqueued_object_class'] = \
        workflow_node.job_queue.enqueued_object_class.split('.')[-1]
    payload['disabled'] = workflow_node.disabled
    payload['overwrite_previous_job'] = workflow_node.overwrite_previous_job
    payload['max_retries'] = workflow_node.max_retries
    payload['batch_size'] = workflow_node.batch_size
    payload['priority'] = workflow_node.priority

    pending_state = RunState.get_pending_state()
    queued_state = RunState.get_queued_state()
    running_state = RunState.get_running_state()
    finished_execution_state = RunState.get_finished_execution_state()
    failed_execution_state = RunState.get_failed_execution_state()
    failed_state = RunState.get_failed_state()
    success_state = RunState.get_success_state()
    process_killed_state = RunState.get_process_killed_state()

    node_jobs = workflow_node.job_set.filter(archived=False)

    payload['number_of_jobs'] = node_jobs.count()
    payload['pending'] = node_jobs.filter(
        run_state=pending_state).count()
    payload['queued'] = node_jobs.filter(
        run_state=queued_state).count()
    payload['running'] = node_jobs.filter(
        run_state=running_state).count()
    payload['finished_execution'] = node_jobs.filter(
        run_state=finished_execution_state).count()
    payload['failed_execution'] = node_jobs.filter(
        run_state=failed_execution_state).count()
    payload['failed'] = node_jobs.filter(
        run_state=failed_state).count()
    payload['success_count'] = node_jobs.filter(
        run_state=success_state).count()
    payload['process_killed'] = node_jobs.filter(
        run_state=process_killed_state).count()

    payload['number_of_jobs_link'] = 'jobs/1/?workflow_node_ids=' + str(workflow_node.id)
    payload['pending_link'] = 'jobs/1/?run_state_ids=' + str(pending_state.id) + '&workflow_node_ids=' + str(workflow_node.id)
    payload['queued_link'] = 'jobs/1/?run_state_ids=' + str(queued_state.id) + '&workflow_node_ids=' + str(workflow_node.id)
    payload['running_link'] = 'jobs/1/?run_state_ids=' + str(running_state.id) + '&workflow_node_ids=' + str(workflow_node.id)
    payload['finished_execution_link'] = 'jobs/1/?run_state_ids=' + str(finished_execution_state.id) + '&workflow_node_ids=' + str(workflow_node.id)
    payload['failed_execution_link'] = 'jobs/1/?run_state_ids=' + str(failed_execution_state.id) + '&workflow_node_ids=' + str(workflow_node.id)
    payload['failed_link'] = 'jobs/1/?run_state_ids=' + str(failed_state.id) + '&workflow_node_ids=' + str(workflow_node.id)
    payload['success_count_link'] = 'jobs/1/?run_state_ids=' + str(success_state.id) + '&workflow_node_ids=' + str(workflow_node.id)
    payload['process_killed_link'] = 'jobs/1/?run_state_ids=' + str(process_killed_state.id) + '&workflow_node_ids=' + str(workflow_node.id)

    result['payload'] = payload


@object_json_response('workflow_node_id', WorkflowNode)
def update_workflow_node(workflow_node, request, result):
    disabled = request.GET.get('disabled')
    overwrite = request.GET.get('overwrite')
    max_retries = request.GET.get('max_retries')
    batch_size = request.GET.get('batch_size')
    priority = request.GET.get('priority')

    if disabled == None:
        result['success'] = False
        result['message'] = 'missing disabled param'
    elif overwrite == None:
        result['success'] = False
        result['message'] = 'missing overwrite param'
    elif max_retries == None:
        result['success'] = False
        result['message'] = 'missing max_retries param'
    elif batch_size == None:
        result['success'] = False
        result['message'] = 'missing batch_size param'
    elif priority == None:
        result['success'] = False
        result['message'] = 'missing priority param'
    else:
        current_disabled = (disabled == 'true')

        prev_disabled = workflow_node.update(
            current_disabled,
            (overwrite == 'true'),
            int(max_retries),
            int(batch_size),
            int(priority))

        #run jobs if this workflow was enabled
        if not workflow_node.workflow.disabled and prev_disabled and not current_disabled:
            run_workflow_node_jobs_signature.delay(workflow_node.id)


@object_json_response('workflow_id', Workflow)
def get_workflow_info(workflow_object, request, result):
    result['payload']['name'] = workflow_object.name
    result['payload']['description'] = workflow_object.description
    result['payload']['disabled'] = workflow_object.disabled


@object_json_all_response(WorkflowNode)
def monitor_workflow(nodes, request, result):
    result['nodes'] = [ str(n) for n in nodes]

    result['edges'] = [ {
        'source': str(n.parent),
        'target': str(n) } for n in nodes
        if n.parent is not None ]

def to_key(s):
    return s.lower().replace(' ', '_')

@object_yaml_all_response(Workflow)
def download_workflow(flows, request, result):
    exes = Executable.objects.filter(archived=False)

    result['executables'] = {}
    for ex in exes:
        k = to_key(ex.name)
        result['executables'][k] = {
            'name': ex.name,
            'path': ex.executable_path,
            'pbs_queue': ex.pbs_queue,
            'pbs_processor': ex.pbs_processor,
            'pbs_walltime': ex.pbs_walltime
        } 

    result['workflows'] = {}
    for f in flows:
        k = to_key(f.name)
        result['workflows'][k] = {
            "ingest": f.ingest_strategy_class,
            "states": [],
            "graph": []
        }

        states = result['workflows'][k]['states']
        for n in f.workflownode_set.filter(archived=False):
            states.append({
                'key': to_key(n.job_queue.name),
                'label': n.job_queue.name,
                'class': n.job_queue.job_strategy_class,
                'enqueued_class': n.job_queue.enqueued_object_class,
                'executable': to_key(n.job_queue.executable.name)
            })

        graph = result['workflows'][k]['graph']
        head = f.workflownode_set.filter(
            archived=False,
            is_head=True).first()
        work_list = deque()

        current = head
        try:
            while current:
                children = current.get_children()
                children_keys = [to_key(c.job_queue.name) for c in children]
                if current.is_head or (len(children_keys) > 0):
                    graph.append([to_key(current.job_queue.name), children_keys])
                    for c in children:
                        if c not in work_list:
                            work_list.append(c)
                current = work_list.popleft()
        except IndexError:
            pass

    del result['message']
    del result['payload']
    del result['success']


@object_json_response(id_name='workflow_id', clazz=Workflow)
def update_workflow(workflow_object, request, response):
    name = request.GET.get('name')
    description = request.GET.get('description')
    current_disabled = (request.GET.get('disabled') == 'true')

    prev_disabled = workflow_object.update(
        name, description, current_disabled)

    #run jobs if this workflow was enabled
    if prev_disabled and not current_disabled:
        WorkflowController.run_workflow_nodes(workflow_object)
