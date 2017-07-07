from django.http import JsonResponse
from workflow_engine.models import *

def check_if_finished(request):
    result = {}
    success = True
    message = ''
    payload = {}
    number_of_manual_running_jobs = 0
    finished_jobs = 0

    try:
        tasks = Task.objects.filter(run_state=RunState.get_running_state(), archived=False)
        for task in tasks:
            strategy = task.get_strategy()
            if strategy.is_manual_strategy():
                number_of_manual_running_jobs+= ONE

                if strategy.check_if_task_finished(task):
                    finished_jobs+= ONE

        payload['number_of_manual_running_jobs'] = number_of_manual_running_jobs
        payload['finished_jobs'] = finished_jobs

    except Exception as e:
            success = False
            message = str(e)
        
    result['success'] = success
    result['message'] = message
    result['payload'] = payload

    return JsonResponse(result)