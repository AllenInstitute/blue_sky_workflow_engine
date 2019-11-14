from kombu import Exchange, Queue
import logging

class SimpleRouter(object):
    _log = logging.getLogger('workflow_engine.simple_router')
    # Note the values are sets, not dicts
    base_dict = {
        'ingest': {
            'ingest_task',
        },
        'moab_status': {
            'check_moab_status'
        },
        'moab': {
            'submit_moab_task',
            'kill_moab_task',
            'run_task'
        },
        'circus_status': {
            'check_circus_task_status'
        },
        'circus_remote_status': {
            'check_remote_status'
        },
        'circus': {
            'submit_worker_task',
            'check_circus_status'
        },
        'mock': {
            'submit_mock_task',
        },
        'workflow': {
            'create_job',
            'queue_job',
            'kill_job',
            'enqueue_next_queue',
            'run_workflow_node_jobs_by_id',
            'set_jobs_for_run_by_id',
        },
        'result': { 
            'process_pbs_id',
            'process_running',
            'process_failed',
            'process_finished_execution',
            'process_failed_execution'
        },
        'broadcast': { 
            'update_dashboard'
        }
    }

    def __init__(self, app_name, blue_green='blue'):
        self.app_name = app_name
        self.blue_green = blue_green
        self.routing_dict = SimpleRouter.invert_route_dict(
            SimpleRouter.base_dict,
            app_name
        )
        self.exchange = {
            'blue': Exchange(
                "{}__{}".format(app_name, 'blue'),
                type='direct'),
            'green': Exchange(
                "{}__{}".format(app_name, 'green'),
                type='direct')
        }

    @classmethod
    def invert_route_dict(cls, routing_dict, app_name=None):
        if app_name is not None:
            suffix = "@{}".format(app_name)
        else:
            suffix = ""

        inverted_route_dict = {}

        for q,task_names in routing_dict.items():
            queue_name = "{}{}".format(q, suffix)

            inverted_route_dict.update(
                { task_name: queue_name for task_name in task_names })

        return inverted_route_dict

    def route_task(self, name, args, kwargs,
                  options, task=None, **kw):
        del args    # unused
        del kwargs  # unused
        del task    # unused
        del kw      # unused

        task_name = name.split('.')[-1]
        SimpleRouter._log.info('ROUTING: {}'.format(options))

        try:
            q = self.routing_dict.get(task_name)
            SimpleRouter._log.info(
                'Routing task %s to %s', task_name, q
            )
        except:
            SimpleRouter._log.error(
                'Unknown task {}'.format(task_name))
            q = 'null'

        SimpleRouter._log.info('q: {}'.format(q))

        return {
            'exchange': '{}__{}'.format(
                self.app_name,
                self.blue_green),
            'queue': q
        }

    def task_queues(self, worker_names):
        queues =  [
            Queue(
                "{}@{}".format(worker_name, self.app_name),
                self.exchange[self.blue_green],
                routing_key=worker_name,
                queue_arguments={'x-max-priority': 10}
            )
            for worker_name in worker_names
        ]
        node_exchange = Exchange(
            'workflow_nodes',
            routing_key='at_em.#',
            type='topic')
        if 'workflow' in worker_names:
            queues.append(
                Queue(
                    'at_em.#',
                    node_exchange,
                    routing_key='at_em.#',
                    queue_arguments={'x-max-priority': 10}
                )
            )

        return queues

