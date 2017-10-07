import yaml
import logging
#import importlib
from workflow_engine.models import \
    Workflow, Executable, WorkflowNode, JobQueue, RunState


class WorkflowConfig:
    _log = logging.getLogger('workflow_engine.workflow_config')

    def __init__(self, n, s, g, l):
        self.name = n
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

        
        workflow_definition = definition['workflows']

        for k,v in workflow_definition.items():
            parents = {}
            
            for gs in v['graph']:
                parent = gs[0]
                children = gs[1]
                for child in children:
                    parents[child] = parent
            
            states = {}
            state_list = []
            for s in v['states']:
                state = {
                    'key': s['key'], 
                    'label': s['label'],
                    'parent': None
                }
                
                if s['key'] in parents:
                    state['parent'] = parents[s['key']]

                if 'manual' in s and s['manual'] is True:
                    state['manual'] = True
                else:
                    state['manual'] = False

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

                states[s['key']] = state
                state_list.append(s['key'])

            workflows['flows'].append(
                cls(k, states, v['graph'], state_list))

        return workflows

    @classmethod
    def from_yaml_file(cls, path):
        with open(path, 'r') as f:
            return cls.from_yaml(f)


    @classmethod
    def create_workflow(cls, app_package, workflows_yml):
    
        pbs_queue = 'mindscope'
        pbs_processor = 'vmem=16g',
        pbs_walltime = 'walltime=5:00:00'
        wc = cls.from_yaml_file(workflows_yml)
        
        null_executable =  Executable(name='Null Executable',
                           description='Error Case',
                           executable_path='/lorem/ipsum',
                           pbs_queue='NULLQUEUE',
                           pbs_processor='ERROR',
                           pbs_walltime='ERROR')
        null_executable.save()

        executables = { 'None': null_executable}
        
        for k, e in wc['executables'].items():
            executables[k] = \
                Executable(name=e['name'],
                           description='N/A',
                           executable_path=e['path'],
                           pbs_queue=e['pbs_queue'],
                           pbs_processor=e['pbs_processor'],
                           pbs_walltime=e['pbs_walltime'])
            executables[k].save()
        
        
        for run_state_name in wc['run_states']:
            RunState(name=run_state_name).save()
    
        for workflow_spec in wc['flows']:
            workflow_name = workflow_spec.name
    
            workflow = Workflow(name=workflow_name,
                                description='N/A',
                                use_pbs=False)
            workflow.save()
                
            nodes = {}
            nodes[None] = None
            nodes['None'] = None
    
            for k in workflow_spec.state_list:
                node = workflow_spec.states[k]
                
                queue_name = '%s %s' % (workflow_name, node['label'])
                WorkflowConfig._log.info(
                    "Creating job queue %s %s %s %s" % (
                        queue_name,
                        node['class'],
                        node['enqueued_class'],
                        node['executable']))
    
                queue = JobQueue(name=queue_name,
                                 job_strategy_class=str(node['class']),
                                 enqueued_object_class=node['enqueued_class'],
                                 executable=executables[node['executable']])
   
                queue.save()
    
                batch_size = 1
                max_retries = 1

                WorkflowConfig._log.info(
                    "parent: %s->%s %s" % (node['key'],
                                           node['parent'],
                                           str(nodes[node['parent']])))

                if node['parent'] in nodes and node['parent'] in nodes:
                    parent_node = nodes[node['parent']]
                    head = False
                else:
                    parent_node = None
                    head = True

                nodes[node['key']] = \
                    WorkflowNode(job_queue=queue,
                                 parent=parent_node,
                                 is_head=head,
                                 workflow=workflow,
                                 batch_size=batch_size,
                                 max_retries=max_retries)

                nodes[node['key']].save()
