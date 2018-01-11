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
from django.http import JsonResponse
from django.http import HttpResponse
from django.template import loader
from workflow_engine.models.executable import Executable
from workflow_engine.models import ONE
from workflow_engine.views import shared, HEADER_PAGES


context = {
    'pages': HEADER_PAGES,
}

def executables_page(request, page, url=None):
    executable_ids = request.GET.get('executable_ids')
    names = request.GET.get('names')
    pbs_queues = request.GET.get('pbs_queues')
    pbs_processors = request.GET.get('pbs_processors')
    pbs_walltimes = request.GET.get('pbs_walltimes')

    sort = request.GET.get('sort')

    if url is None:
        url = request.get_full_path()

    set_params = False

    if executable_ids != None:
        records = Executable.objects.filter(id__in=executable_ids.split(','))
        set_params = True
    else:
        records = Executable.objects.all()

    if names != None:
        records = records.filter(name__in=(names.split(',')))
        set_params = True

    if pbs_queues != None:
        records = records.filter(pbs_queue__in=(pbs_queues.split(',')))
        set_params = True

    if pbs_processors != None:
        records = records.filter(pbs_processor__in=(pbs_processors.split(',')))
        set_params = True

    if pbs_walltimes != None:
        records = records.filter(pbs_walltime__in=(pbs_walltimes.split(',')))
        set_params = True

    if sort == None:
        sort = '-updated_at'
    
    records = records.order_by(sort)

    add_sort_executable(context, sort, url, set_params)
    shared.add_context(context, records, url, page, 'executables')

    template = loader.get_template('executables.html')
    shared.add_settings_info_to_context(context)
    return HttpResponse(template.render(context, request))

def executables(request):
    url = request.get_full_path() + '/1/'

    return executables_page(request, ONE, url)

def get_executable_names(request):
    result = {}
    success = True
    payload = []
    message = ''

    try:
        executables = Executable.objects.all().order_by('name')
        for executable in executables:
            payload.append(executable.name)

    except Exception as e:
            success = False
            message = str(e)
        
    result['success'] = success
    result['message'] = message
    result['payload'] = payload

    return JsonResponse(result)

def add_sort_executable(context, sort, url, set_params):
    context['sort'] = sort
    context['id_sort'] = shared.sort_helper('id', sort, url, set_params)
    context['name_sort'] = shared.sort_helper('name', sort, url, set_params)
    context['description_sort'] = shared.sort_helper('description', sort, url, set_params)
    context['executable_path_sort'] = shared.sort_helper('executable_path', sort, url, set_params)
    context['static_arguments_sort'] = shared.sort_helper('static_arguments', sort, url, set_params)
    context['pbs_processor_sort'] = shared.sort_helper('pbs_processor', sort, url, set_params)
    context['pbs_walltime_sort'] = shared.sort_helper('pbs_walltime', sort, url, set_params)
    context['pbs_queue_sort'] = shared.sort_helper('pbs_queue', sort, url, set_params)
    context['created_at_sort'] = shared.sort_helper('created_at', sort, url, set_params)
    context['updated_at_sort'] = shared.sort_helper('updated_at', sort, url, set_params)