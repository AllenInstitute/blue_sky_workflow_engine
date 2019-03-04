from circus import get_arbiter
import os

# TODO: these should not just be docker paths
app_name = 'blue_sky'
base_dir = os.environ.get('BASE_DIR', '/blue_sky')
_CELERY_PATH = '/opt/conda/bin/celery'
_BASE_ENV = {
    'WORKFLOW_CONFIG_YAML': '/blue_sky/config/workflow_config.yml',
    'APP_PACKAGE': app_name,
    'MESSAGE_QUEUE_HOST': 'ibs-timf-ux1.corp.alleninstitute.org',
    'MESSAGE_QUEUE_PORT': '9008',
    'BLUE_SKY_SETTINGS': '/blue_sky/config/docker_blue_sky_settings.yml',
    'PATH': '/opt/conda/envs/circus/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
    'PYTHONPATH': '/blue_sky:/blue_sky_workflow_engine'
}


def celery_command_string(worker_name, app_name):
    return " ".join((
        _CELERY_PATH,
        "-A",
        "workflow_engine.celery.{}_tasks".format(worker_name),
        "worker --concurrency=1 --loglevel=info",
        "-n {}@{}".format(worker_name, app_name))
    )


def debug_log_path(base_dir, worker_name):
    return os.path.join(
        base_dir,
        'logs',
        '{}.log'.format(worker_name))

def dmerge(d1, d2):
    d = d1.copy()
    d.update(d2)

    return d


django_env = dmerge(_BASE_ENV, {
    'DJANGO_SETTINGS_MODULE': 'blue_sky.settings'
})

arbiter_list = [
    {
        'cmd': (
            "/bin/bash -c "
            "'source /opt/conda/bin/activate base; "
            "python -m workflow_engine.ui_server'"
        ),
        "env": dmerge(django_env, {
            'DEBUG_LOG': debug_log_path(base_dir, 'ui')
        }), 
        'numprocesses': 1
    },
    {
        'cmd': ' '.join([
            '/bin/bash -c',
            '"source /opt/conda/bin/activate base;',
            'sleep 60;',
            'python -m celery flower',
            '--url_prefix=flower --backend=rpc://',
            '--broker=amqp://blue_sky_user:blue_sky_user@${MESSAGE_QUEUE_HOST}:${MESSAGE_QUEUE_PORT}',
            '-n flower@{} --port=5557"'.format(app_name)
        ]),
        "env": dmerge(django_env, {
            'DEBUG_LOG': debug_log_path(base_dir, 'flower')
        }), 
        'numprocesses': 1
    },
    {
        'cmd': (
            'python -m celery '
            '-A workflow_client.tasks.circus_test worker '
            '--concurrency=1 --loglevel=info -n circus@{}'
        ).format(app_name),
        "env": dmerge(_BASE_ENV, {
            'DEBUG_LOG': debug_log_path(base_dir, 'circus')
        }), 
        'numprocesses': 1
    },
    {
        'cmd': (
            '/bin/bash -c '
            '"source activate nb; '
            'cd /blue_sky/notebooks; '
            'python -m manage shell_plus --notebook"'
        ),
        "env": dmerge(django_env, {
            'DEBUG_LOG': debug_log_path(base_dir, 'nb')
        }), 
        'numprocesses': 1
    },
    {
        'cmd': (
            '/bin/bash -c '
            '"source /opt/conda/bin/activate base; '
            'python -m celery '
            '-A workflow_engine.celery.moab_beat beat '
            '--broker=amqp://blue_sky_user:blue_sky_user@${MESSAGE_QUEUE_HOST}:${MESSAGE_QUEUE_PORT}"'
        ),
        "env": dmerge(django_env, {
            'DEBUG_LOG': debug_log_path(base_dir, 'beat')
        }), 
        'numprocesses': 1
    }
]

for worker_name in [
        'result',
        'ingest',
        'workflow',
        'moab',
        'moab_status',
        'circus_status',
        'local',
        'monitor',
    ]:
    arbiter_list.extend([
        {
            "cmd": (
                '/bin/bash -c '
                '"source /opt/conda/bin/activate base; {}"'
            ).format(
                celery_command_string(worker_name, app_name)
            ),
            "env": dmerge(django_env, {
                'DEBUG_LOG': debug_log_path(base_dir, worker_name),
            }),
            "numprocesses": 1
        }])

print(arbiter_list)

arbiter = get_arbiter(arbiter_list)

try:
    arbiter.start()
finally:
    arbiter.stop()