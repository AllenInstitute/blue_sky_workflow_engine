# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2017. Allen Institute. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Redistributions for commercial purposes are not permitted without the
# Allen Institute's written permission.
# For purposes of this license, commercial purposes is the incorporation of the
# Allen Institute's software into anything for which you will charge fees or
# other compensation. Contact terms@alleninstitute.org for commercial licensing
# opportunities.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
from django.conf import settings
from django.http import HttpResponse
from django.template import loader
from workflow_engine.views import shared, HEADER_PAGES
import django
import sys
import workflow_engine

context = {
    'pages': HEADER_PAGES,
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
    context['workflow_version']  = workflow_engine.__version__
    context['python_version']  = get_python_version()
    context['django_version']  = django.get_version()
    context['database_host'] = settings.DATABASES['default']['HOST']
    context['database_name'] = settings.DATABASES['default']['NAME']
    context['database_port'] = settings.DATABASES['default']['PORT']
    context['results_per_page']  = settings.RESULTS_PER_PAGE

    context['flower_monitor_url'] = settings.FLOWER_MONITOR_URL
    context['rabbit_monitor_url'] = settings.RABBIT_MONITOR_URL
    context['message_queue_host']  = '---'
    context['admin_url'] = settings.ADMIN_URL

    context['seconds_between_refresh'] = 300
    shared.add_settings_info_to_context(context)
    
    template = loader.get_template('job_grid.html')
    return HttpResponse(template.render(context, request))