# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2018-2019. Allen Institute. All rights reserved.
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
from django.contrib.contenttypes.models import ContentType
from workflow_engine.import_class import import_class
import yaml
import logging


class WorkflowConfig:
    _log = logging.getLogger('workflow_engine.workflow_config')

    def __init__(self, n, i, s, g, l):
        self.name = n
        self.ingest_strategy = i
        self.states = s
        self.state_list = l
        self.num_states = len(s)
        self.next_states = [list(i) for i in g]
        #self.pairs = self.transition_pairs_from_table()

    @classmethod
    def from_yaml(cls, y):
        definition = yaml.load(y)
        workflows = {
            'run_states': definition['run_states'],
            'executables': definition['executables'],
            'flows': []
        }

        for e in workflows['executables'].values():
            if 'remote_queue' not in e:
                e['remote_queue'] = 'default'
            if 'environment' not in e:
                e['environment'] = []

        workflow_definitions = definition['workflows']

        for k,wf_def in workflow_definitions.items():
            parents = {}
            
            for gs in wf_def['graph']:
                parent = gs[0]
                children = gs[1]
                for child in children:
                    if child not in parents:
                        parents[child] = [ parent ]
                    else:
                        parents[child].append(parent)
                        
            WorkflowConfig._log.info("parent dict: %s" % (str(parents)))

            states = {}
            state_list = []
            for s in wf_def['states']:
                state = {
                    'key': s['key'], 
                    'label': s['label'],
                    'parents': []
                }
                
                if s['key'] in parents:
                    state['parents'] = parents[s['key']]

                if 'workflow' in s and s['workflow'] is True:
                    state['workflow'] = True
                else:
                    state['workflow'] = False

                if 'class' in s:
                    state['class'] = s['class']
                else:
                    state['class'] = None

                if 'enqueued_class' in s:
                    state['enqueued_class'] = s['enqueued_class']
                else:
                    state['enqueued_class'] = 'None'

                if 'executable' in s:
                    state['executable'] = s['executable']
                else:
                    state['executable'] = 'None'

                if 'batch_size' in s:
                    state['batch_size'] = s['batch_size']
                else:
                    state['batch_size'] = 1

                states[s['key']] = state
                state_list.append(s['key'])

            ingest = wf_def.get('ingest', None)

            workflows['flows'].append(
                cls(k, ingest, states, wf_def['graph'], state_list))

        return workflows

    @classmethod
    def from_yaml_file(cls, path):
        with open(path, 'r') as f:
            return cls.from_yaml(f)


    @classmethod
    def create_workflow(cls, workflows_yml):
        workflow_config = cls.from_yaml_file(workflows_yml)

        null_executable, created = \
            Executable.objects.get_or_create(
                name='Null Executable',
                defaults={
                    'description': 'Error Case',
                    'executable_path': '/lorem/ipsum',
                    'static_arguments': None,
                    'environment': '',
                    'remote_queue': 'default',
                    'pbs_queue': 'NULLQUEUE',
                    'pbs_processor': 'ERROR',
                    'pbs_walltime': 'ERROR'})

        executables = { 'None': null_executable}
        
        for k, e in workflow_config['executables'].items():
            if 'args' in e:
                args = ' '.join(e['args'])
            else:
                args = None

            executables[k], _ = \
                Executable.objects.update_or_create(
                    name=e['name'],
                    archived=False,
                    defaults= {
                        'description': 'N/A',
                        'executable_path': e['path'],
                        'static_arguments': args,
                        'environment': ';'.join(e['environment']),
                        'remote_queue': e['remote_queue'],
                        'pbs_queue': e['pbs_queue'],
                        'pbs_processor': e['pbs_processor'],
                        'pbs_walltime': e['pbs_walltime']})
        
        for run_state_name in workflow_config['run_states']:
            RunState.objects.update_or_create(
                name=run_state_name)
    
        for workflow_spec in workflow_config['flows']:
            workflow_name = workflow_spec.name
    
            workflow, _ = \
                Workflow.objects.update_or_create(
                    name=workflow_name,
                    archived=False,
                    defaults={
                        'description': 'N/A',
                        'ingest_strategy_class': workflow_spec.ingest_strategy,
                        'use_pbs': False})
                
            nodes = {}
            nodes[None] = None
            nodes['None'] = None

            for k in workflow_spec.state_list:
                node = workflow_spec.states[k]

                queue_name = node['label'] # TODO: check for uniqueness

                WorkflowConfig._log.info(
                    "Creating job queue %s %s %s %s" % (
                        queue_name,
                        node['class'],
                        node['enqueued_class'],
                        node['executable']))

                eoc = import_class(node['enqueued_class'])
                eo_content_type = ContentType.objects.get_for_model(eoc)

                queue, _ = \
                    JobQueue.objects.update_or_create(
                        name=queue_name,
                        archived=False,
                        defaults={
                            'job_strategy_class': str(node['class']),
                            'enqueued_object_type': eo_content_type,
                            'executable': executables[node['executable']]})
    
                batch_size = node['batch_size']
                max_retries = 1

                nodes[node['key']], _ = \
                    WorkflowNode.objects.update_or_create(
                        job_queue=queue,
                        parent=None,
                        is_head=False,
                        workflow=workflow,
                        archived=False,
                        defaults={
                            'batch_size': batch_size,
                            'max_retries': max_retries})

            for k in workflow_spec.state_list:
                node = workflow_spec.states[k]
                queue_name = node['label']

                # For now only use the first parent
#                parent_key = next(iter(node['parents']), None)
                for parent_key in iter(node['parents']):

                    if parent_key in nodes and parent_key is not None:
                        parent_node = nodes[parent_key]
                        head = False
                    else:
                        parent_node = None
                        head = True
# 
                    # TODO: deprecated
                    nodes[node['key']].parent = parent_node
                    nodes[node['key']].is_head = head
                    nodes[node['key']].save()

                    WorkflowEdge.objects.update_or_create(
                        workflow=workflow,
                        source=parent_node,
                        sink=nodes[node['key']],
                        disabled=False,
                        archived=False
                    )

                    WorkflowConfig._log.info(
                        "edge: %s->%s %s" % (node['key'],
                                               parent_key,
                                               str(nodes[parent_key])))

    @classmethod
    def archive_all_workflows(cls):
        for queue in JobQueue.objects.filter(archived=False):
            queue.archive()
        for node in WorkflowNode.objects.filter(archived=False):
            node.archive()
        for exe in Executable.objects.filter(archived=False):
            exe.archive()
        for flow in Workflow.objects.filter(archived=False):
            flow.archive()
        for edge in WorkflowEdge.objects.filter(archived=False):
            edge.archive()
        # RunState.objects.all().delete()  # TODO: runstates are in regular config.

# circular imports?
from workflow_engine.models import (
    JobQueue,
    Executable,
    WorkflowNode,
    WorkflowEdge,
    Workflow,
    RunState
)