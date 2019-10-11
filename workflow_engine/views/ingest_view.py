from django.http import JsonResponse
from workflow_engine.signatures import ingest_signature
import json
import traceback
import logging

_log = logging.getLogger('workflow_engine.views.ingest_view')

def ingest(request, workflow_name=None, tag=None, format=None):
    result = {
        'success': True,
        'message': '',
        'payload': {} 
        }

    try:
        if format is not None and format != 'json':
            result['success'] = False
            result['message'] = 'Only json format is currently supported'
            return JsonResponse(result)

        if request.method == 'POST':
            result['message'] = workflow_name
            body = json.loads(request.body.decode('utf-8'))
            if tag is not None:
                tags = [ tag ]
            else:
                tags = []
            _log.info('sending ingest ' + workflow_name + ' ' + str(body))

            celery_result = ingest_signature.delay(
                workflow_name, body, tags)

            response_message = celery_result.wait(10)
            result['message'] = response_message
        else:
            result['message'] = 'please use POST'
            return JsonResponse(result, status=405)
    except Exception as e:
            result['success'] = False
            result['message'] = str(e) + ' - ' + str(traceback.format_exc())

    return JsonResponse(result, status=200)
