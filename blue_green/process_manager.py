from circus import get_arbiter
from time import sleep
import argparse
import os

_CELERY_PATH = '/opt/conda/bin/celery'
_ACTIVATE_PATH = '/opt/conda/bin/activate'
_FLOWER_DELAY = 1
_FLOWER_PORT = 5557


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


def get_arbiter_list(app_name, bg_conda_env, base_dir):
    _BASE_ENV = {
        'WORKFLOW_CONFIG_YAML': '/blue_sky/config/workflow_config.yml',
        'APP_PACKAGE': app_name,
        'MESSAGE_QUEUE_HOST': 'em-131db',
        'MESSAGE_QUEUE_PORT': '9038',
        'BLUE_SKY_SETTINGS': '/green/blue_sky_settings.yml',
        'PATH': '/opt/conda/envs/circus/bin:/opt/conda/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
        'PYTHONPATH': '/{}:{}:/{}/blue_sky_workflow_engine:/render_modules'.format(bg, base_dir, bg)
        #    'PYTHONPATH': '/{}:/{}/blue_sky_workflow_engine:/render_modules'.format(bg,  bg)
    }

    django_env = dmerge(_BASE_ENV, {
        'DJANGO_SETTINGS_MODULE': 'settings' # in BG dir
    })
    
    arbiter_list = [
        {
            'cmd': ' '.join((
                "/bin/bash -c ",
                "'source {} {}; ".format(_ACTIVATE_PATH, bg_conda_env),
                "python -m workflow_engine.ui_server'"
            )),
            "env": dmerge(django_env, {
                'DEBUG_LOG': debug_log_path(base_dir, 'ui')
            }), 
            'numprocesses': 1
        },
        {
            'cmd': ' '.join([
                '/bin/bash -c',
                '"source {} {};'.format(_ACTIVATE_PATH, bg_conda_env),
                'sleep {};'.format(_FLOWER_DELAY),
                'python -m celery flower',
                '--url_prefix=flower --backend=rpc',
                '--broker=amqp://blue_sky_user:blue_sky_user@${MESSAGE_QUEUE_HOST}:${MESSAGE_QUEUE_PORT}',
                '-n flower@{} --port={}"'.format(app_name, _FLOWER_PORT)
            ]),
            "env": dmerge(django_env, {
                'DEBUG_LOG': debug_log_path(base_dir, 'flower')
            }), 
            'numprocesses': 1
        },
        {
            'cmd': ' '.join((
                '/bin/bash -c',
                '"source {} {}_circus; '.format(_ACTIVATE_PATH, bg),
                'unset DJANGO_SETTINGS_MODULE; ',
                'python -m celery ',
                '-A workflow_client.tasks.circus_test worker ',
                '--concurrency=1 --loglevel=info -n circus@{}"'
            )).format(app_name),
            "env": dmerge(_BASE_ENV, {
                'DEBUG_LOG': debug_log_path(base_dir, 'circus')
            }), 
            'numprocesses': 1
        },
        {
            'cmd': ' '.join((
                '/bin/bash -c ', '"source {} {}; '.format(_ACTIVATE_PATH, bg_conda_env),
                'cd /{}/notebooks; '.format(bg),
                'python -m manage shell_plus --notebook"'
            )),
            "env": dmerge(django_env, {
                'DEBUG_LOG': debug_log_path(base_dir, 'nb')
            }), 
            'numprocesses': 1
        },
        {
            'cmd': ' '.join((
                '/bin/bash -c ',
                '"source {} {}; '.format(_ACTIVATE_PATH, bg_conda_env),
                'python -m celery ',
                '-A workflow_engine.celery.moab_beat beat ',
                '--broker=amqp://blue_sky_user:blue_sky_user@${MESSAGE_QUEUE_HOST}:${MESSAGE_QUEUE_PORT}"')),
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

    return arbiter_list

if __name__ == '__main__':

    # TODO: these should not just be docker paths
    app_name = 'at_em_imaging_workflow'
    bg = 'green'
    bg_conda_env = bg
    base_dir = os.environ.get(
        'BASE_DIR', '/{}/{}'.format(bg, app_name))

    arbiter_list = get_arbiter_list(
        app_name,
        bg,
        base_dir)

    print(arbiter_list)

    arbiter = get_arbiter(
        arbiter_list, 
        controller='tcp://127.0.0.1:9055',
        pubsub_endpoint='tcp://127.0.0.1:9056'
    )

    try:
        arbiter.start()
    finally:
        arbiter.stop()
