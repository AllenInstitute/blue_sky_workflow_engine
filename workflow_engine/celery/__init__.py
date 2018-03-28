from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from workflow_client.client_settings import load_settings_yaml, config_object

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proj.settings')

app = Celery('workflow_engine.workflow_client')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
#app.config_from_object('django.conf:settings', namespace='CELERY')
settings = load_settings_yaml()
app.config_from_object(config_object(settings))

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
