from circus import get_arbiter
from time import sleep
import argparse
import copy
import os
import sys

_CELERY_PATH = '/conda_envs/py_37/bin/celery'
_ACTIVATE_PATH = '/conda_envs/py_37/bin/activate'
_FLOWER_DELAY = 1
_FLOWER_PORT = 5557
_MESSAGE_BROKER = (
    'amqp://${MESSAGE_QUEUE_USER}:${MESSAGE_QUEUE_PASS}'
    '@${MESSAGE_QUEUE_HOST}:${MESSAGE_QUEUE_PORT}/${MESSAGE_QUEUE_VHOST}'
)

def celery_command_string(worker_name, app_name):
    return " ".join((
        _CELERY_PATH,
        "-A",
        "workflow_engine.celery.{}_tasks".format(worker_name),
        "worker --concurrency=1 --loglevel=info",
        "-n {}@{}".format(worker_name, app_name))
    )


def debug_log_path(log_dir, worker_name):
    return os.path.join(
        log_dir,
        '{}.log'.format(worker_name))

def dmerge(d1, d2):
    d = d1.copy()
    d.update(d2)

    return d

_BASE_ENV = {
    'WORKFLOW_CONFIG_YAML':
        os.environ.get(
            'WORKFLOW_CONFIG_YAML',
            '/blue_sky/config/workflow_config.yml'),
    'MESSAGE_QUEUE_USER':
        os.environ.get(
            'MESSAGE_QUEUE_USER',
            'blue_sky_user'),
    'MESSAGE_QUEUE_PASS':
        os.environ.get(
            'MESSAGE_QUEUE_PASS',
            'blue_sky_user'),
    'MESSAGE_QUEUE_HOST':
        os.environ.get(
            'MESSAGE_QUEUE_HOST',
            'message_queue'),
    'MESSAGE_QUEUE_PORT':
        os.environ.get(
            'MESSAGE_QUEUE_PORT',
            str(5672)),
    'MESSAGE_QUEUE_VHOST':
        os.environ.get(
            'MESSAGE_QUEUE_VHOST',
            ''),
    'BLUE_SKY_SETTINGS':
        os.environ.get(
            'BLUE_SKY_SETTINGS',
            '/green/blue_sky_settings.yml'),
    'MOAB_AUTH': os.environ.get('MOAB_AUTH', ':'),
    'PATH': '/conda_envs/circus/bin:/conda_envs/circus/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
}

def get_arbiter_list(app_name, bg, base_dir, log_dir='/logs'):
    bg_conda_env = '/conda_envs/py_37'
    base_env = copy.deepcopy(_BASE_ENV)
    base_env['APP_PACKAGE'] = app_name
    base_env['PYTHONPATH'] = '/blue_green:/blue_sky_workflow_engine:/{}:{}:/{}/blue_sky_workflow_engine:/render_modules:/EM_aligner_python'.format(bg, base_dir, bg)
    #    base_env['PYTHONPATH'] = '/{}:/{}/blue_sky_workflow_engine:/render_modules'.format(bg,  bg)
    django_env = dmerge(base_env, {
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
                'DEBUG_LOG': debug_log_path(log_dir, 'ui')
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
                '--broker={}'.format(_MESSAGE_BROKER),
                '-n flower@{} --port={}"'.format(app_name, _FLOWER_PORT)
            ]),
            "env": dmerge(django_env, {
                'DEBUG_LOG': debug_log_path(log_dir, 'flower')
            }), 
            'numprocesses': 1
        },
#        {
#            'cmd': ' '.join((
#                '/bin/bash -c',
#                '"source {} {}_circus; '.format(_ACTIVATE_PATH, bg),
#                'unset DJANGO_SETTINGS_MODULE; ',
#                'python -m celery ',
#                '-A workflow_client.tasks.circus_test worker ',
#                '--broker={}'.format(_MESSAGE_BROKER),
#                '--concurrency=1 --loglevel=info ',
#                '-n circus@{}'.format(app_name),
#                '"'
#            )),
#            "env": dmerge(base_env, {
#                'DEBUG_LOG': debug_log_path(log_dir, 'circus'),
#                'BLUE_SKY_APP_NAME': app_name
#            }), 
#            'numprocesses': 1
#        },
        {
            'cmd': ' '.join((
                '/bin/bash -c ', '"source {} {}; '.format(_ACTIVATE_PATH, bg_conda_env),
                'cd /{}/notebooks; '.format(bg),
                'python -m manage shell_plus --notebook"'
            )),
            "env": dmerge(django_env, {
                'DEBUG_LOG': debug_log_path(log_dir, 'nb')
            }), 
            'numprocesses': 1
        },
        {
            'cmd': ' '.join((
                '/bin/bash -c ',
                '"source {} {}; '.format(_ACTIVATE_PATH, bg_conda_env),
                'python -m celery ',
                '-A workflow_engine.celery.moab_beat beat ',
                '--broker={}"'.format(_MESSAGE_BROKER))),
            "env": dmerge(django_env, {
                'DEBUG_LOG': debug_log_path(log_dir, 'beat')
            }), 
            'numprocesses': 1
        }
    ]
    
    for worker_name in (
             'result',
             'ingest',
             'workflow',
             'moab',
             'moab_status',
             'mock',
             'circus_status',
             #'local',
             #'monitor',
        ):
        arbiter_list.extend([
            {
                "cmd": (
                    '/bin/bash -c '
                    '"source /conda_envs/py_37/bin/activate {}; {}"'
                ).format(
                    bg_conda_env,
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
    app_name = sys.argv[-2]
    bg = sys.argv[-1]
    bg_conda_env = bg
    base_dir = os.environ.get(
        'BASE_DIR', '/{}/{}'.format(bg, app_name))
    log_dir = '/logs'

    arbiter_list = get_arbiter_list(
        app_name,
        bg,
        base_dir,
        log_dir)

    arbiter = get_arbiter(
        arbiter_list, 
        controller='tcp://127.0.0.1:9055',
        pubsub_endpoint='tcp://127.0.0.1:9056'
    )

    try:
        arbiter.start()
    finally:
        arbiter.stop()
