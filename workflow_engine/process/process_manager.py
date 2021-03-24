from circus import get_arbiter
import copy
import os
import sys
import yaml
import click

_APP_NAME='blue_sky'
_CONDA_ENVS = '/conda_envs'
_CELERY_PATH = os.path.join(
    _CONDA_ENVS,
    'py_36/bin/celery'
)
_ACTIVATE_PATH = 'activate'
_FLOWER_DELAY = 1
_FLOWER_PORT = 5557

def celery_command_string(worker_name, app_name):
    return " ".join((
        _CELERY_PATH,
        "-A",
        "workflow_engine.process.workers.{}_tasks".format(worker_name),
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
    'BLUE_SKY_SETTINGS':
        os.environ.get(
            'BLUE_SKY_SETTINGS',
            '/home/blue_sky_user/work/blue_sky_settings.yml'),
    'MOAB_AUTH': os.environ.get('MOAB_AUTH', ':'),
    'PATH': '{}/circus/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'.format(_CONDA_ENVS),
}


try:
    with open(_BASE_ENV['BLUE_SKY_SETTINGS']) as f:
        settings_dict = yaml.load(f, Loader=yaml.SafeLoader)
        _MESSAGE_BROKER = settings_dict['broker_url']
except:
    _MESSAGE_BROKER = 'pyamqp://blue_sky_user:blue_sky_user@message_queue:5672/'



def get_arbiter_list(app_name, workdir, log_dir=None, python_path=None):
    if log_dir is None:
        log_dir = os.path.join(workdir, 'logs')

    bg_conda_env = os.path.join(_CONDA_ENVS, 'py_36')
    base_env = copy.deepcopy(_BASE_ENV)
    base_env['APP_PACKAGE'] = app_name
    base_env['PYTHONPATH'] = python_path

    django_env = dmerge(base_env, {
        'DJANGO_SETTINGS_MODULE': 'blue_sky.settings' # in PYTHONPATH
    })
    
    arbiter_list = [
        {
            'cmd': ' '.join((
                "/bin/bash -c ",
                "'source /opt/conda/etc/profile.d/conda.sh ; conda {} {}; ".format(_ACTIVATE_PATH, bg_conda_env),
                "python -m workflow_engine.process.workers.ui_server'"
            )),
            "env": dmerge(django_env, {
                'DEBUG_LOG': debug_log_path(log_dir, 'ui')
            }), 
            'use_fds': True,
            'numprocesses': 1
        },
        {
            'cmd': ' '.join([
                '/bin/bash -c',
                '"source /opt/conda/etc/profile.d/conda.sh; conda {} {};'.format(_ACTIVATE_PATH, bg_conda_env),
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
#                '/bin/bash -l -c',
#                '"source {} {}_circus; '.format(_ACTIVATE_PATH, bg),
#                'unset DJANGO_SETTINGS_MODULE; ',
#                'python -m celery ',
#                '-A workflow_engine.process.workers.circus_test worker ',
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
                '/bin/bash -c',
                '"source /opt/conda/etc/profile.d/conda.sh; conda {} {};'.format(_ACTIVATE_PATH, bg_conda_env),
                'cd {}/notebooks; '.format(workdir),
                'python -m workflow_engine.management.manage shell_plus --notebook"'
            )),
            "env": dmerge(django_env, {
                'DEBUG_LOG': debug_log_path(log_dir, 'nb')
            }), 
            'numprocesses': 1
        },
        # {
        #     'cmd': ' '.join((
        #         '/bin/bash -l -c ',
        #         '"source {} {}; '.format(_ACTIVATE_PATH, bg_conda_env),
        #         'python -m celery ',
        #         '-A workflow_engine.process.workers.job_start_beat_tasks beat"',
        #     )),
        #     "env": dmerge(django_env, {
        #         'DEBUG_LOG': debug_log_path(log_dir, 'beat')
        #     }), 
        #     'numprocesses': 1
        # },
    ]

    for worker_name in (
             'result',
             'ingest',
             'workflow',
             'moab',
             'mock',
        ):
        arbiter_list.extend([
            {
                "cmd": (
                    '/bin/bash -c '
                    '"source /opt/conda/etc/profile.d/conda.sh; conda {} {}; {}"'
                ).format(
                    _ACTIVATE_PATH,
                    bg_conda_env,
                    celery_command_string(worker_name, app_name)
                ),
                "env": dmerge(django_env, {
                    'DEBUG_LOG': debug_log_path(log_dir, worker_name),
                }),
                "numprocesses": 1
            }])

    return arbiter_list


@click.command()
@click.option('--app_name', default='blue_sky', help='blue sky application package')
@click.option('--workdir', default='/source/blue_sky', help='directory where processes should be launched')
@click.option('--log_dir', default='/home/blue_sky_user/work/logs', help='directory where log files are stored')
@click.option('--controller', default='tcp://127.0.0.1:9055', help='circusd controller uri')
@click.option('--pubsub_endpoint', default='tcp://127.0.0.1:9056', help='circus pubsub endpoint uri')
@click.option('--python_path', default='/source/blue_sky:/source/blue_sky_workflow_engine:', help='circus pubsub endpoint uri')
def main(app_name, workdir, log_dir, controller, pubsub_endpoint, python_path):
    if python_path is None:
        python_path = "/source/at_em_imaging_workflow:/source/blue_sky_workflow_engine:/render_modules:/EM_aligner_python:"

    arbiter_list = get_arbiter_list(
        app_name,
        workdir,
        log_dir,
        python_path=(':'.join([python_path, workdir]))
    )

    arbiter = get_arbiter(
        arbiter_list, 
        controller=controller,
        pubsub_endpoint=pubsub_endpoint
    )

    try:
        arbiter.start()
    finally:
        arbiter.stop()


if __name__ == '__main__':
    main()
