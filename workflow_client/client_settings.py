import os
import yaml


class settings_attr_dict(dict):
    __getattr__ = dict.get


def load_settings_yaml():
    settings_dict = {}

    try: 
        blue_sky_settings_json = \
            os.getenv('BLUE_SKY_SETTINGS')

        with open(blue_sky_settings_json) as f:
            settings_dict = settings_attr_dict(yaml.load(f))
    except:
        raise Exception('need to set BLUE_SKY_SETTINGS')

    return settings_dict


def get_message_broker_url(celery_settings):
    return 'pyamqp://%s:%s@%s:%s//' % (
        celery_settings.MESSAGE_QUEUE_USER,
        celery_settings.MESSAGE_QUEUE_PASSWORD,
        celery_settings.MESSAGE_QUEUE_HOST,
        celery_settings.MESSAGE_QUEUE_PORT)


def config_object(s):
    return settings_attr_dict({
        'broker_url': get_message_broker_url(s),
        'result_backend': 'rpc://',
        'task_serializer': 'json',
        'result_serializer': 'json',
        'accept_content': ['json'],
        'timezone': 'US/Pacific',
        'enable_utc': True,
        #'task_queues': [ 'ingest' ],
        'task_default_queue': s.DEFAULT_MESSAGE_QUEUE_NAME
    })

# settings = load_settings_yaml()
