import os
import yaml


class _settings_attr_dict(dict):
    __getattr__ = dict.get


def load_settings_yaml():
    settings_dict = {}

    try: 
        blue_sky_settings_json = \
            os.getenv('BLUE_SKY_SETTINGS')

        with open(blue_sky_settings_json) as f:
            settings_dict = _settings_attr_dict(yaml.load(f))
    except:
        pass
        # raise Exception('need to set BLUE_SKY_SETTINGS')

    return settings_dict

def config_object(s):
    return _settings_attr_dict({
        'broker_url': 'pyamqp://%s:%s@%s:%s//' % (
            s.MESSAGE_QUEUE_USER,
            s.MESSAGE_QUEUE_PASSWORD,
            s.MESSAGE_QUEUE_HOST,
            s.MESSAGE_QUEUE_PORT),
        'result_backend': 'rpc://',
        'task_serializer': 'json',
        'result_serializer': 'json',
        'accept_content': ['json'],
        'timezone': 'US/Pacific',
        'enable_utc': True,
        'task_queues': [ 'ingest' ],
        'task_default_queue': s.DEFAULT_MESSAGE_QUEUE_NAME
    })

# settings = load_settings_yaml()
