from django.conf import settings
from django.http import HttpResponse
from workflow_engine.models import *
from django.template import loader
from workflow_engine.views import shared
import django
import sys

pages = ['index', 'jobs', 'workflows', 'workflow_creator', 'job_queues', 'executables']
context = {
    'pages': pages,
}

ZERO = 0
ONE = 1
TWO = 2
MILLISECONDS_IN_SECOND = 1000

def get_python_version():
    info = sys.version_info
    return str(info.major) + '.' + str(info.minor) + '.' + str(info.micro)

def index(request):
    context['selected_page'] = 'index'
    context['base_path'] = settings.BASE_FILE_PATH
    context['workflow_version']  = settings.WORKFLOW_VERSION
    context['python_version']  = get_python_version()
    context['django_version']  = django.get_version()
    context['database_host'] = settings.DATABASES['default']['HOST']
    context['database_name'] = settings.DATABASES['default']['NAME']
    context['database_port'] = settings.DATABASES['default']['PORT']
    context['results_per_page']  = settings.RESULTS_PER_PAGE
    context['message_queue_host']  = settings.MESSAGE_QUEUE_HOST
    context['seconds_between_refresh'] = settings.MILLISECONDS_BETWEEN_REFRESH / MILLISECONDS_IN_SECOND
    shared.add_settings_info_to_context(context)
    
    template = loader.get_template('index.html')
    return HttpResponse(template.render(context, request))