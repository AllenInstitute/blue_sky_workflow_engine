from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from workflow_client.client_settings import load_settings_yaml, config_object
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj.settings')

app = Celery('blue_sky',
             broker_url='pyamqp://{}:{}@{}:{}//'.format(
                 settings.MESSAGE_QUEUE_USER,
                 settings.MESSAGE_QUEUE_PASSWORD,
                 settings.MESSAGE_QUEUE_HOST,
                 settings.MESSAGE_QUEUE_PORT)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
#app.config_from_object('django.conf:settings', namespace='CELERY')
blue_sky_settings = load_settings_yaml()
app.config_from_object(config_object(blue_sky_settings))

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
