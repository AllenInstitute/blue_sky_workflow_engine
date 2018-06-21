# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2018. Allen Institute. All rights reserved.
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
import logging
import traceback
from django.core.exceptions import FieldDoesNotExist
from django.http.response import HttpResponse
import yaml 


_log = logging.getLogger('workflow_engine.views.decorators')


def object_yaml_all_response(clazz):
    def decor(fn):
        def wrapper(request):
            result = {
                'success': True,
                'message': '',
                'payload': {} 
                }

            try:
                try:
                    clazz._meta.get_field('archived')
                    objects = clazz.objects.filter(archived=False)
                except FieldDoesNotExist:
                    objects = clazz.objects.all()
                fn(objects, request, result)
            except Exception as e:
                    result['success'] = False
                    result['message'] = str(e) + ' - ' + str(traceback.format_exc())

            return HttpResponse(
                yaml.dump(result, default_flow_style=False),
                content_type="application/x-yaml")

        return wrapper
    return decor


def object_json_all_response(clazz):
    def decor(fn):
        def wrapper(request):
            result = {
                'success': True,
                'message': '',
                'payload': {} 
                }

            try:
                try:
                    clazz._meta.get_field('archived')
                    objects = clazz.objects.filter(archived=False)
                except FieldDoesNotExist:
                    objects = clazz.objects.all()
                fn(objects, request, result)
            except Exception as e:
                    result['success'] = False
                    result['message'] = str(e) + ' - ' + str(traceback.format_exc())

            return JsonResponse(result)

        return wrapper
    return decor


def object_json_response(id_name, clazz):
    def decor(fn):
        ids_name = id_name + 's'

        def wrapper(request):
            result = {
                'success': True,
                'message': '',
                'payload': {} 
                }

            try:
                if id_name in request.GET:
                    object_ids = [ request.GET.get(id_name) ]
                elif ids_name in request.GET:
                    object_ids = request.GET.get(ids_name).split(',')

                if object_ids is not None:
                    records = clazz.objects.filter(id__in=object_ids)
                    for job_object in records:
                        fn(job_object, request, result)
                else:
                    result['success'] = False
                    result['message'] = 'Missing ' + ids_name
            except Exception as e:
                    result['success'] = False
                    result['message'] = str(e) + ' - ' + str(traceback.format_exc())

            return JsonResponse(result)

        return wrapper
    return decor


def object_json_response2(id_name):
    def decor(fn):
        ids_name = id_name + 's'

        def wrapper(request):
            result = {
                'success': True,
                'message': '',
                'payload': {} 
                }

            try:
                if id_name in request.GET:
                    object_ids = [ request.GET.get(id_name) ]
                elif ids_name in request.GET:
                    object_ids = request.GET.get(ids_name).split(',')
                else:
                    object_ids = None

                if object_ids is not None:
                    fn(object_ids, request, result)
                else:
                    result['success'] = False
                    result['message'] = 'Missing ' + ids_name

                _log.info(result)
            except Exception as e:
                    result['success'] = False
                    mess = str(e) + ' - ' + str(traceback.format_exc())
                    _log.error(mess)
                    result['message'] = mess

            return JsonResponse(result)

        return wrapper
    return decor
