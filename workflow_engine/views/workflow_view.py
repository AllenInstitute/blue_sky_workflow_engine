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
from django.core.exceptions import ObjectDoesNotExist
import traceback
from django.template import loader
from workflow_engine.models import *
from workflow_engine.models.import_class import import_class
from workflow_engine.views import shared
import logging
import json


_log = logging.getLogger('workflow_engine.views.workflow_view')
pages = ['index', 'jobs', 'workflows', 'workflow_creator', 'job_queues', 'executables']
context = {
    'pages': pages,
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
        workflows = Workflow.objects.filter(id__in=workflow_ids.split(','))
    elif workflow_names != None:
        workflows = Workflow.objects.filter(name__in=workflow_names.split(','))
    else:
        workflows = Workflow.objects.all()

    if search_disabled != None:
        workflows = workflows.filter(disabled=shared.string_to_bool(search_disabled))

    if search_use_pbs != None:
        workflows = workflows.filter(use_pbs=shared.string_to_bool(search_use_pbs))

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

        head_workflow_nodes = workflow.get_head_workfow_nodes()
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

def get_workflow_status(request):
    result = {}
    success = True
    message = ''
    payload = {}

    try:
        workflow_node_ids = request.GET.get('workflow_node_ids')
    
        if workflow_node_ids != None:
            records = WorkflowNode.objects.filter(id__in=workflow_node_ids.split(','))

            for record in records:
                job_states = get_job_states(record)
                node_color_class = get_node_color_class(None, None)

                for name in job_states.keys():
                    node_color_class = get_node_color_class(name, node_color_class)

                node_data = {}
                node_data['name'] = record.get_node_name()
                node_data['node_color_class'] = node_color_class

                payload[record.id] = node_data
        else:
            success = False
            message = 'Missing workflow_node_ids'
    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['message'] = message
    result['payload'] = payload

    return JsonResponse(result)

def get_job_states(node):
    result = {}
    
    running_state = RunState.get_running_state()
    pending_state = RunState.get_pending_state()
    queued_state = RunState.get_queued_state()
    finished_execution_state = RunState.get_finished_execution_state()

    success_state = RunState.get_success_state()

    failed_execution_state = RunState.get_failed_execution_state()
    failed_state = RunState.get_failed_state()
    killed_state = RunState.get_process_killed_state()

    success_count = Job.objects.filter(run_state_id__in=[success_state.id], workflow_node_id=node.id, archived=False).count()
    failed_count = Job.objects.filter(run_state_id__in=[failed_execution_state.id, failed_state.id, killed_state.id], workflow_node_id=node.id, archived=False).count()
    running_count = Job.objects.filter(run_state_id__in=[running_state.id, pending_state.id, queued_state.id, finished_execution_state.id], workflow_node_id=node.id, archived=False).count()

    if success_count > ZERO:
        result[success_state.name] = success_count

    if failed_count > ZERO:
        result[failed_state.name] = failed_count

    if running_count > ZERO:
        result[running_state.name] = running_count

    return result

def get_node_content(node):
    job_states = get_job_states(node)

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


def workflow_creator(request):
    context['selected_page'] = 'workflow_creator'
    template = loader.get_template('workflow_creator.html')
    shared.add_settings_info_to_context(context)
    return HttpResponse(template.render(context, request))

def update_pbs(request):
    result = {}
    success = True
    message = ''

    try:
        workflow_id = request.GET.get('workflow_id')
        use_pbs = request.GET.get('use_pbs')

        if workflow_id == None:
            success = False
            message = 'missing workflow_id param'
        elif use_pbs == None:
            success = False
            message = 'missing use_pbs param'
        else:
            workflow = Workflow.objects.get(id=workflow_id)
            use_pbs = (use_pbs == 'true')

            workflow.use_pbs = use_pbs
            workflow.save()

    except ObjectDoesNotExist as e:
        success = False
        message = 'Could not find a workflow record with id of ' + str(workflow_id) 

    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['message'] = message

    return JsonResponse(result)

def get_head_workflow_node_id(request):
    result = {}
    success = True
    message = ''
    payload = None

    try:
        workflow_id = request.GET.get('workflow_id')

        if workflow_id == None:
            success = False
            message = 'missing workflow_id param'
        else:
            head_workflow_node = WorkflowNode.objects.get(is_head=True, workflow_id=workflow_id)
            payload = head_workflow_node.id

    except ObjectDoesNotExist as e:
        success = False
        message = 'Could not find a workflow record with id of ' + str(workflow_id) 

    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['message'] = message
    result['payload'] = payload

    return JsonResponse(result)

def get_enqueued_objects(request):
    result = {}
    success = True
    message = ''
    record_names = []
    record_ids = {}
    priority = None
    enqueued_object_class = None

    try:
        workflow_node_id = request.GET.get('workflow_node_id')

        if workflow_node_id == None:
            success = False
            message = 'missing workflow_node_id param'
        else:
            workflow_node = WorkflowNode.objects.get(id=workflow_node_id)
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

            priority = workflow_node.priority

    except ObjectDoesNotExist as e:
        success = False
        message = 'Could not find a workflow record with id of ' + str(workflow_id) 

    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['message'] = message
    result['record_names'] = record_names
    result['record_ids'] = record_ids
    result['priority'] = priority
    result['enqueued_object_class'] = enqueued_object_class

    return JsonResponse(result)

def create_job(request):
    result = {}
    success = True
    message = ''

    try:
        priority = request.GET.get('priority')
        enqueued_object_id = request.GET.get('enqueued_object_id')
        workflow_node_id = request.GET.get('workflow_node_id')

        if priority == None:
            success = False
            message = 'missing priority param'
        elif enqueued_object_id == None:
            success = False
            message = 'missing enqueued_object_id param'
        elif workflow_node_id == None:
            success = False
            message = 'missing workflow_node_id param'
        else:
            workflow_node = WorkflowNode.objects.get(id=workflow_node_id)
            job = Job()
            job.enqueued_object_id=enqueued_object_id
            job.workflow_node=workflow_node
            job.run_state=RunState.get_pending_state()
            job.priority = priority
            job.save()
            job.run_jobs()

    except ObjectDoesNotExist as e:
        success = False
        message = 'Could not find a workflow record with id of ' + str(workflow_id) 

    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['message'] = message

    return JsonResponse(result)

def get_node_info(request):
    result = {}
    payload = {}
    success = True
    message = ''

    try:
        workflow_node_id = request.GET.get('workflow_node_id')

        if workflow_node_id == None:
            success = False
            message = 'missing workflow_node_id param'
        else:
            workflow_node = WorkflowNode.objects.get(id=workflow_node_id)
            payload['job_queue'] = workflow_node.job_queue.name
            payload['job_queue_link'] = 'job_queues?job_queue_ids=' + str(workflow_node.job_queue.id)
            try:
                payload['executable'] = workflow_node.job_queue.executable.name
                payload['executable_link'] = 'executables?executable_ids=' + str(workflow_node.job_queue.executable.id)
            except:
                payload['executable'] = ''
                payload['executable_link'] = ''
            
            payload['enqueued_object_class'] = workflow_node.job_queue.enqueued_object_class
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

            number_of_jobs = Job.objects.filter(workflow_node_id=workflow_node_id, archived=False).count()
            pending = Job.objects.filter(workflow_node_id=workflow_node_id, run_state=pending_state, archived=False).count()
            queued = Job.objects.filter(workflow_node_id=workflow_node_id, run_state=queued_state, archived=False).count()
            running = Job.objects.filter(workflow_node_id=workflow_node_id, run_state=running_state, archived=False).count()
            finished_execution = Job.objects.filter(workflow_node_id=workflow_node_id, run_state=finished_execution_state, archived=False).count()
            failed_execution = Job.objects.filter(workflow_node_id=workflow_node_id, run_state=failed_execution_state, archived=False).count()
            failed = Job.objects.filter(workflow_node_id=workflow_node_id, run_state=failed_state, archived=False).count()
            success_count = Job.objects.filter(workflow_node_id=workflow_node_id, run_state=success_state, archived=False).count()
            process_killed = Job.objects.filter(workflow_node_id=workflow_node_id, run_state=process_killed_state, archived=False).count()

            payload['number_of_jobs'] = number_of_jobs
            payload['pending'] = pending
            payload['queued'] = queued
            payload['running'] = running
            payload['finished_execution'] = finished_execution
            payload['failed_execution'] = failed_execution
            payload['failed'] = failed
            payload['success_count'] = success_count
            payload['process_killed'] = process_killed

            payload['number_of_jobs_link'] = 'jobs/1/?workflow_node_ids=' + workflow_node_id
            payload['pending_link'] = 'jobs/1/?run_state_ids=' + str(pending_state.id) + '&workflow_node_ids=' + workflow_node_id
            payload['queued_link'] = 'jobs/1/?run_state_ids=' + str(queued_state.id) + '&workflow_node_ids=' + workflow_node_id
            payload['running_link'] = 'jobs/1/?run_state_ids=' + str(running_state.id) + '&workflow_node_ids=' + workflow_node_id
            payload['finished_execution_link'] = 'jobs/1/?run_state_ids=' + str(finished_execution_state.id) + '&workflow_node_ids=' + workflow_node_id
            payload['failed_execution_link'] = 'jobs/1/?run_state_ids=' + str(failed_execution_state.id) + '&workflow_node_ids=' + workflow_node_id
            payload['failed_link'] = 'jobs/1/?run_state_ids=' + str(failed_state.id) + '&workflow_node_ids=' + workflow_node_id
            payload['success_count_link'] = 'jobs/1/?run_state_ids=' + str(success_state.id) + '&workflow_node_ids=' + workflow_node_id
            payload['process_killed_link'] = 'jobs/1/?run_state_ids=' + str(process_killed_state.id) + '&workflow_node_ids=' + workflow_node_id

    except ObjectDoesNotExist as e:
        success = False
        message = 'Could not find a workflow node record with id of ' + str(workflow_node_id) 

    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['payload'] = payload
    result['message'] = message

    return JsonResponse(result)

def update_workflow_node(request):
    result = {}
    payload = {}
    success = True
    message = ''

    try:
        workflow_node_id = request.GET.get('workflow_node_id')
        disabled = request.GET.get('disabled')
        overwrite = request.GET.get('overwrite')
        max_retries = request.GET.get('max_retries')
        batch_size = request.GET.get('batch_size')
        priority = request.GET.get('priority')

        if workflow_node_id == None:
            success = False
            message = 'missing workflow_node_id param'
        elif disabled == None:
            success = False
            message = 'missing disabled param'
        elif overwrite == None:
            success = False
            message = 'missing overwrite param'
        elif max_retries == None:
            success = False
            message = 'missing max_retries param'
        elif batch_size == None:
            success = False
            message = 'missing batch_size param'
        elif priority == None:
            success = False
            message = 'missing priority param'
        else:
            workflow_node = WorkflowNode.objects.get(id=workflow_node_id)

            current_disabled = (disabled == 'true')
            prev_disabled = workflow_node.disabled

            workflow_node.disabled = current_disabled
            workflow_node.overwrite_previous_job = (overwrite == 'true')
            workflow_node.max_retries = int(max_retries)
            workflow_node.batch_size = int(batch_size)
            workflow_node.priority = int(priority)

            workflow_node.save()

            workflow_node.run_workflow_node_jobs()

            #run jobs if this workflow was enabled
            if not workflow_node.workflow.disabled and prev_disabled and not current_disabled:
                workflow_node.run_workflow_node_jobs()

    except ObjectDoesNotExist as e:
        success = False
        message = 'Could not find a workflow node record with id of ' + str(workflow_node_id) 

    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['payload'] = payload
    result['message'] = message

    return JsonResponse(result)

def get_workflow_info(request):
    result = {}
    payload = {}
    success = True
    message = ''

    try:
        workflow_id = request.GET.get('workflow_id')

        if workflow_id == None:
            success = False
            message = 'missing workflow_id param'
        else:
            workflow = Workflow.objects.get(id=workflow_id)
            payload['name'] = workflow.name
            payload['description'] = workflow.description
            payload['disabled'] = workflow.disabled

    except ObjectDoesNotExist as e:
        success = False
        message = 'Could not find a workflow record with id of ' + str(workflow_id) 

    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['payload'] = payload
    result['message'] = message

    return JsonResponse(result)

def update_workflow(request):
    result = {}
    payload = {}
    success = True
    message = ''

    try:
        workflow_id = request.GET.get('workflow_id')
        name = request.GET.get('name')
        description = request.GET.get('description')
        disabled = request.GET.get('disabled')

        if workflow_id == None:
            success = False
            message = 'missing workflow_id param'
        elif name == None:
            success = False
            message = 'missing name param'
        elif disabled == None:
            success = False
            message = 'missing disabled param'
        else:
            workflow = Workflow.objects.get(id=workflow_id)

            current_disabled = (disabled == 'true')
            prev_disabled = workflow.disabled

            if description == '':
                description = None

            workflow.name = name
            workflow.description = description
            workflow.disabled = current_disabled
            workflow.save()

            #run jobs if this workflow was enabled
            if prev_disabled and not current_disabled:
                for workflow_node in WorkflowNode.objects.filter(workflow=workflow):
                    if not workflow_node.disabled:
                        workflow_node.run_workflow_node_jobs()

    except ObjectDoesNotExist as e:
        success = False
        message = 'Could not find a workflow record with id of ' + str(workflow_id) 

    except Exception as e:
            success = False
            message = str(e) + ' - ' + str(traceback.format_exc())
        
    result['success'] = success
    result['payload'] = payload
    result['message'] = message

    return JsonResponse(result)
