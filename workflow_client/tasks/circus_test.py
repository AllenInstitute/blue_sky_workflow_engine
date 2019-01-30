#from workflow_engine.celery.job_status.circus_status import CircusStatus
import celery
from circus.process import Process
from circus.client import CircusClient
from workflow_client.tasks.circus_status import CircusStatus
import traceback
from workflow_client.simple_router import SimpleRouter
import simplejson as json
import logging.config
import jinja2
import stat
import os

app_name = 'circus_test'
broker_url='amqp://blue_sky_user:blue_sky_user@ibs-timf-ux1.corp.alleninstitute.org:9008'

_log = logging.getLogger(
    'workflow_engine.celery.circus_worker'
)

@celery.signals.after_setup_task_logger.connect
def after_setup_celery_task_logger(logger, **kwargs):
    logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'class': 'logging.Formatter',
            'format': '%(asctime)s %(name)-15s %(levelname)-8s %(processName)-10s %(message)s'
        }
    },    
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'detailed',
            'filename': os.environ.get('DEBUG_LOG',
                                       'logs/debug.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'WARN',
            'propagate': True,
        },
        'blue_sky': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'workflow_engine': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'workflow_client': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'celery.task': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        }
    }
})


class CircusProcessTask(celery.Task):
    _num_processes = 100
    _PROCESS_DICT = {}
    _PROC_ID = 10000
    _client = CircusClient(endpoint='tcp://127.0.0.1:5655')


app = celery.Celery(
    app_name,
    backend='rpc://',
    broker=broker_url)
app.conf.imports = (
    'workflow_engine.celery.error_handler',
)
router = SimpleRouter("blue_sky")
app.conf.task_queues = router.task_queues('circus')
app.conf.task_routes = ( 
    router.route_task,
)

#@celery.shared_task(
#    name='workflow_engine.celery.circus_tasks.submit_worker_task',
#    base=CircusProcessTask,
#    bind=True,
#    trail=True)
def submit_circus_task_new(
    self,
    name,
    executable_path,
    args,
    working_dir,
    environment
):
    try:
        task_id = CircusProcessTask._PROC_ID

        p = CircusProcessTask._client.call("""
    {
        "command": "add",
        "properties": {
            "cmd": "%s",
            "name": "%s",
            "options": {
            "copy_env": true,
            "stdout_stream": {
                "filename": "stdout.log"
            },
            "stderr_stream": {
                "filename": "stderr.log"
            }
            },
            "start": true
        }
    }
    """ % (executable_path, task_id))
        CircusProcessTask._PROCESS_DICT[
            str(CircusProcessTask._PROC_ID)
        ] = p
        CircusProcessTask._PROC_ID = CircusProcessTask._PROC_ID + 1

        return str(task_id)
    except Exception as e:
        _log.error(e)
        return "Error {}".format(e)

def generate_task_script(
        script_file,
        executable_file,
        static_args,
        input_file,
        output_file,
        working_dir,
        conda_env='root',
        env_vars=None
    ):
    if env_vars is None:
        env_vars=dict()

    if static_args is None:
        static_args = ''

    template_args = {
        'conda_env': conda_env,
        'env_vars': env_vars,
        'python_executable': executable_file, # /opt/conda/envs/circus/bin/python
        'static_args': static_args,
        'args': "--input_json {} --output_json {}".format(
            input_file, output_file
        )
    }
    
    env = jinja2.Environment(
        loader=jinja2.DictLoader({
            'python_conda': """#!/bin/bash
source /opt/conda/bin/activate {{ conda_env }}

{% for evar in env_vars %}
export {{ evar }}
{% endfor %}

rm exit_code.txt
{{ python_executable }} {{ static_args }} {{ args }} 2>&1 > output.log
echo $? > exit_code.txt
"""
    }))

    # TODO: refactor out of this function
    bash_template = env.get_template('python_conda')

    with open(script_file, 'w') as f:
        f.write(bash_template.render(**template_args))

    st = os.stat(script_file)
    os.chmod(script_file, st.st_mode | stat.S_IEXEC | stat.S_IREAD)


@celery.shared_task(
    name='workflow_engine.celery.circus_tasks.submit_worker_task',
    base=CircusProcessTask,
    bind=True,
    trail=True)
def submit_circus_task(
    self,
    name,
    script_file,
    executable_path,
    input_file,
    output_file,
    args,
    working_dir,
    environment
):
    conda_env = environment.get('CONDA_ENV', 'root')

    env_vars = ['{}={}'.format(k,v) for k,v in environment.items()]

    try:
        generate_task_script(
            script_file,
            executable_path,
            args,
            input_file,
            output_file,
            working_dir,
            conda_env,
            env_vars
        )
    except Exception as e:
        _log.error(e)

    call_args = [
        name,
        name,
        '/bin/bash'
    ]
    kwargs={
        'args': [ script_file ],
        'working_dir': working_dir,
        'env': environment,
        #'use_fds':True,
        #'shell':True
    }

    _log.info(str(call_args) + " " + str(kwargs))

    try:
        task_id = CircusProcessTask._PROC_ID
        p = Process(*call_args, **kwargs)
        CircusProcessTask._PROCESS_DICT[
            str(CircusProcessTask._PROC_ID)
        ] = p
        CircusProcessTask._PROC_ID = CircusProcessTask._PROC_ID + 1

        return str(task_id)
    except Exception as e:
        _log.error(str(e) + ' - ' + str(traceback.format_exc()))
        return "Error {}".format(e)


@celery.shared_task(
    base=CircusProcessTask,
    bind=True,
    trail=True)
def submit_task_orig(self, countdown):
    try:
        task_id = CircusProcessTask._PROC_ID
        p = Process(
            "Example",
            "task_{}".format(CircusProcessTask._PROC_ID),
            "/opt/conda/envs/circus/bin/python",
            args=["-m", "example", str(countdown)]
        )
        CircusProcessTask._PROCESS_DICT[
            str(CircusProcessTask._PROC_ID)
        ] = p
        CircusProcessTask._PROC_ID = CircusProcessTask._PROC_ID + 1
    
        return str(task_id)
    except Exception as e:
        return "Error {}".format(e)


@celery.shared_task(
    base=CircusProcessTask,
    bind=True,
    trail=True)
def kill_task(self, task_id):
    try:
        _log.info(CircusProcessTask._PROCESS_DICT)
        proc = CircusProcessTask._PROCESS_DICT[str(task_id)]
        proc.stop()

        return 'OK'
    except Exception as e:
        _log.error(str(e) + ' - ' + str(traceback.format_exc()))
        return "Error {}".format(e)


@celery.shared_task(
    base=CircusProcessTask,
    bind=True,
    trail=True)
def task_stdout(self, task_id):
    try:
        proc = CircusProcessTask._PROCESS_DICT[str(task_id)]

        stdout_str = []
        for l in proc.stdout:
            stdout_str.append("".join(chr(x) for x in bytearray(l)))

        return '\n'.join(stdout_str)
    except Exception as e:
        return "Error {}".format(e)

@celery.shared_task(
    base=CircusProcessTask,
    bind=True,
    trail=True)
def task_stderr(self, task_id):
    try:
        proc = CircusProcessTask._PROCESS_DICT[str(task_id)]

        stderr_str = []
        for l in proc.stderr:
            stderr_str.append("".join(chr(x) for x in bytearray(l)))

        return '\n'.join(stderr_str)
    except Exception as e:
        return "Error {}".format(e)


@celery.shared_task(
    base=CircusProcessTask,
    name='workflow_engine.check_remote_status',
    bind=True,
    trail=True
)
def check_remote_status(self, running_task_dicts):
    CircusStatus('circus').send_remote_status_results(
        running_task_dicts
    )
    #    'circus'
    #).send_remote_status_results()

@celery.shared_task(
    base=CircusProcessTask,
    name='workflow_engine.check_circus_status'
)
def check_status():
    statuses = {
        i: p.info() for i,p in CircusProcessTask._PROCESS_DICT.items()
    }
    for i,p in CircusProcessTask._PROCESS_DICT.items():
        try:
            statuses[i]['status'] = p.status
        except:
            pass

    for i,p in CircusProcessTask._PROCESS_DICT.items():
        try:
            statuses[i]['working_dir'] = p.working_dir
        except:
            pass

        try:
            with open(
                os.path.join(
                    p.working_dir,
                    'exit_code.txt'),
                'r') as f:
                exit_code = int(f.readline().strip())
                statuses[i]['exit_code'] = exit_code
        except:
            try:
                statuses[i]['exit_code'] = None
            except:
                pass

    _log.info(json.dumps(statuses, indent=2))

    return statuses


@celery.shared_task(
    base=CircusProcessTask,
    name='workflow_engine.inspect_circus',
    bind=True,
    trail=True
)
def inspect(self):
    infos = {
        i: p.info() for i,p in CircusProcessTask._PROCESS_DICT.items()
    }

    return infos

