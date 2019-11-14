from workflow_engine.models import (
    Executable,
    JobQueue,
    Workflow,
    WorkflowEdge,
    WorkflowNode
)
import json
from builtins import classmethod


class WorkflowJsonSerializer(object):
    @classmethod
    def load_workflow(cls, filepath):
        with open(filepath, 'r') as f:
            config = json.load(f)

        exes = {}
        for k, e in config['executables'].items():
            exes[k] = Executable.objects.get_or_create(
                name=e['name'],
                defaults={
                    "description": e.get("description", None),
                    "executable_path": e["path"],
                    "static_arguments": ' '.join(e.get("args", [])),
                    "environment": ';'.join(e.get("environment", [])),
                    "remote_queue": e.get("remote_queue", "default"),
                    "pbs_queue": e.get("pbs_queue", "pbs"),
                    "pbs_processor": e.get("pbs_processor", ''),
                    "pbs_walltime": e.get("pbs_walltime", '')
                })[0]
        
            for c in e['configurations']:
                exes[k].configurations.update_or_create(
                    name=c["name"],
                    configuration_type=c["type"],
                    defaults={
                        "json_object": c["json"]
                    }
                )
        
        workflows = {}
        queues = {}
        nodes = {}
        
        for k, w in config['workflows'].items():
            workflows[k] = Workflow.objects.get_or_create(
                name=k,
                defaults={
                    "ingest_strategy_class": w["ingest"]
                }
            )[0]
        
            for s in w['states']:
                q = s['key']
                queues[q] = JobQueue.objects.get_or_create(
                    name=s['label'],
                    defaults={
                        "job_strategy_class": s['class'],
                        "executable": exes[s["executable"]]
                    }
                )[0]
        
                nodes[q] = WorkflowNode.objects.get_or_create(
                    job_queue=queues[q],
                    workflow=workflows[k],
                    defaults={
                        "batch_size": s.get('batch_size', 1),
                        "priority": s.get('priority', 50),
                        "max_retries": s.get('max_retries', 0),
                        "overwrite_previous_job": s.get('overwrite_previous_job', True)
                    }
                )[0]
        
                for nc in s['configurations']:
                    nodes[q].configurations.update_or_create(
                        name=nc["name"],
                        configuration_type=nc["type"],
                        defaults={
                            "json_object": nc["json"]
                        }
                    )
        
        for k, w in config['workflows'].items():
            for e in w['edges']:
                if e[0] and e[1]:
                    WorkflowEdge.objects.get_or_create(
                        workflow=workflows[k],
                        source=nodes[e[0]],
                        sink=nodes[e[1]]
                    )[0]


    @classmethod
    def serialize_workflow(cls):
        config = {
            'executables': {},
            'workflows': {}
        }
        
        for e in Executable.objects.all():
            ex_name = e.name
            ex_key = ex_name.lower().replace(' ', '_')
            config['executables'][ex_key] = {
                "name": e.name,
                'description': e.description,
                "path": e.executable_path,
                "args": (e.static_arguments.split(" ") if e.static_arguments else []),
                "environment": (e.environment.split(";") if e.environment else []),
                "remote_queue": e.remote_queue,
                "pbs_processor": e.pbs_processor,
                "pbs_walltime": e.pbs_walltime,
                "pbs_queue": e.pbs_queue,
                "version": e.version,
                "configurations": [
                    {
                        "name": c.name,
                        "type": c.configuration_type,
                        "json": c.json_object
                    }
                    for c in e.configurations.all()
                ]
            }
        
        for w in Workflow.objects.all():
            config['workflows'][w.name] = {
                "ingest": w.ingest_strategy_class,
                "states": [ {
                    "key": n.job_queue.name.lower().replace(' ', '_'),
                    "label": n.job_queue.name,
                    "class": n.job_queue.job_strategy_class,
                    "enqueued_class": n.job_queue.enqueued_object_type.model,
                    "executable": n.job_queue.executable.name.lower().replace(' ', '_'),
                    "batch_size": n.batch_size,
                    "priority": n.priority,
                    "overwrite_previous_job": n.overwrite_previous_job,
                    "max_retries": n.max_retries,
                    "configurations": [
                        {
                            "name": c.name,
                            "type": c.configuration_type,
                            "json": c.json_object
                        }
                        for c in n.configurations.all()
                    ]
                } for n in w.workflownode_set.all() ],
                "edges": [
                    [ e.source.job_queue.name.lower().replace(' ', '_') if e.source else None,
                      e.sink.job_queue.name.lower().replace(' ', '_') if e.sink else None ] for e in w.workflowedge_set.all()
                ]
            }
            
        
        return json.dumps(config, indent=2)
