from django.http import HttpResponse
from workflow_engine.file_holder import FileHolder
from workflow_engine.log_holder import LogHolder
from django.template import loader
from workflow_engine.models import *
from workflow_engine.views import shared

pages = ['index', 'jobs', 'workflows', 'workflow_creator', 'job_queues', 'executables']
context = {
    'pages': pages,
}

def logs(request):
    types = request.GET.get('types')
    task_id = request.GET.get('task_id')
    executable_id = request.GET.get('executable_id')
    job_id = request.GET.get('job_id')
    job_queue_id = request.GET.get('job_queue_id')

    include_input_file = False
    include_output_file = False
    include_executable_file = False
    include_log_file = False
    include_command = False
    error_message = ''
    contained_error = False

    context['log_holders'] = [] 

    if job_id != None:
        try:
            job = Job.objects.get(id=job_id)
            tasks = job.get_tasks()
            for task in tasks:
                log_holder = get_task_log_holder(task.id, types, context)
                if log_holder != None:
                    context['log_holders'].append(log_holder)

        except Exception as e:
            error_message = 'Something went wrong: ' + str(e)
            contained_error = True

    elif task_id != None:
        log_holder = get_task_log_holder(task_id, types, context)
        if log_holder != None:
            context['log_holders'].append(log_holder)

    elif executable_id != None:
       log_holder = get_executable_log_holder(executable_id, context)
       if log_holder != None:
            context['log_holders'].append(log_holder)
    elif job_queue_id != None:
        job_queue = JobQueue.objects.get(id=job_queue_id)
        executable_id = job_queue.executable.id
        log_holder = get_executable_log_holder(executable_id, context)
        if log_holder != None:
            context['log_holders'].append(log_holder)
    else:
        contained_error = True
        error_message = 'Missing parameter'

    template = loader.get_template('logs.html')
    shared.add_settings_info_to_context(context)
    return HttpResponse(template.render(context, request))

def get_executable_log_holder(executable_id, context):
    log_holder = None

    try:
        executable = Executable.objects.get(id=executable_id)

        log_holder = LogHolder()
        log_holder.executable_id = executable_id
        log_holder.executable_name = executable.name

        executable_file = get_executable_file(executable.executable_path)
        log_holder.executable_file = log_holder.add_file_holder(FileHolder(executable_file, 'Executable'))

    except Exception as e:
        context['error_message'] = 'Something went wrong: ' + str(e)
        context['contained_error'] = True
        context['log_holder'] = None

    return log_holder

def get_task_log_holder(task_id, types, context):
    log_holder = None

    try:
        task = Task.objects.get(id=task_id)
        include_command = False
        include_log_file = False
        include_input_file = False
        include_output_file = False
        include_executable_file = False
        include_pbs_file = False

        log_holder = LogHolder()
        log_holder.task_id = task_id

        if types == None:
            include_input_file = True
            include_output_file = True
            include_log_file = True
            include_command = True
            include_pbs_file = True
        else:
            for type_value in types.split(','):
                if type_value == 'input_file':
                    include_input_file = True

                elif type_value == 'output_file':
                    include_output_file = True

                elif type_value == 'executable':
                    include_executable_file = True

                elif type_value == 'log':
                    include_log_file = True

                elif type_value == 'command':
                    include_command = True

                elif type_value == 'pbs':
                    include_pbs_file = True

        if include_command:
            log_holder.full_executable = task.full_executable

        if include_log_file:
            log_holder.add_file_holder(FileHolder(task.log_file, 'Log', task.start_run_time))

        if include_input_file:
            log_holder.add_file_holder(FileHolder(task.input_file, 'Input', task.start_run_time))

        if include_output_file:
            log_holder.add_file_holder(FileHolder(task.output_file, 'Output', task.start_run_time))

        if include_executable_file:
            executable_file = get_executable_file(task.full_executable)
            log_holder.add_file_holder(FileHolder(executable_file, 'Executable', task.start_run_time))

        if include_pbs_file:
            log_holder.add_file_holder(FileHolder(task.pbs_file, 'Pbs', task.start_run_time))

        job_queue = task.get_job_queue()
        log_holder.job_queue_name = job_queue.name
        log_holder.job_queue_id = job_queue.id

        executable = task.get_executable()
        if executable != None:
            log_holder.executable_id = executable.id
            log_holder.executable_name = executable.name

        log_holder.error_message = FileHolder.add_color_highlighting(task.error_message)

        log_holder.run_state = task.run_state.name
        log_holder.enqueued_object_id = task.enqueued_task_object_id
    except Exception as e:
        context['error_message'] = 'Something went wrong: ' + str(e)
        context['contained_error'] = True
        context['log_holder'] = None


    return log_holder

def get_executable_file(full_executable):
    result = None

    for item in full_executable.split(' '):
        try:
            extension = os.path.splitext(item)[ONE]
        except Exception:
            extension = ''

        if extension == '.py' or extension == '.rb' or extension == '.cpp'  or extension == '.sh':
            result = item

    return result