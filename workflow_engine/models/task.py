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
from django.db import models
from django.utils import timezone
from django.conf import settings
from celery.task.control import revoke
from .job import Job
from .run_state import RunState
from . import ONE, ZERO
from .import_class import import_class
import logging
_model_logger = logging.getLogger('workflow_engine.models')


class Task(models.Model):
    enqueued_task_object_id = models.IntegerField(null=True)
    enqueued_task_object_class = models.CharField(max_length=255, null=True)
    job = models.ForeignKey(Job)
    archived = models.NullBooleanField(default=False)
    run_state = models.ForeignKey(RunState)
    full_executable = models.CharField(max_length=1000, null=True)
    error_message = models.TextField(null=True)
    log_file = models.CharField(max_length=255, null=True)
    input_file = models.CharField(max_length=255, null=True)
    output_file = models.CharField(max_length=255, null=True)
    pbs_file = models.CharField(max_length=255, null=True)
    start_run_time = models.DateTimeField(null=True)
    end_run_time = models.DateTimeField(null=True)
    duration = models.DurationField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    pbs_id = models.CharField(max_length=255, null=True)
    retry_count = models.IntegerField(default=0)
    tags = models.CharField(max_length=255, null=True)

    def __str__(self):
        return 'task: %s (%d)' % (self.full_executable, self.id)

    def get_created_at(self):
        return timezone.localtime(self.created_at).strftime('%m/%d/%Y %I:%M:%S')

    def get_updated_at(self):
        return timezone.localtime(self.updated_at).strftime('%m/%d/%Y %I:%M:%S')

    def set_error_message(self, error_message):

        self.error_message = str(error_message)
        self.save()
        self.job.set_error_message(self.error_message, self)

    def pbs_task(self):
        return self.job.workflow_node.workflow.use_pbs

    def kill_task(self):
        self.set_process_killed_state()
        revoke(self.id, terminate=True)
        strategy = self.get_strategy()
        if strategy.is_execution_strategy():
            strategy.kill_pbs_task(self)

        self.set_end_run_time()

    def get_start_run_time(self):
        result = None
        if self.start_run_time != None:
            result = timezone.localtime(self.start_run_time).strftime('%m/%d/%Y %I:%M:%S')

        return result

    def get_end_run_time(self):
        result = None
        if self.end_run_time != None:
            result = timezone.localtime(self.end_run_time).strftime('%m/%d/%Y %I:%M:%S')

        return result

    def get_enqueued_object_display(self):
        result = None
        try:
            enqueued_object = self.get_enqueued_object()
            result = str(enqueued_object)
        except:
            result = None

        return result

    def get_duration(self):
        result = None
        if self.duration != None:
            total_seconds = self.duration.seconds
            minutes = total_seconds / SECONDS_IN_MIN

            result = str(round(minutes,TWO)) + ' min'

        return result

    def set_start_run_time(self):
        self.start_run_time = timezone.now()
        self.end_run_time = None
        self.duration = None
        self.save()

    def set_end_run_time(self):
        self.end_run_time = timezone.now()
        self.duration = str(self.end_run_time - self.start_run_time)
        self.save()

    def in_failed_state(self):
        run_state_name = self.run_state.name
        return (run_state_name == 'FAILED' or
                run_state_name == 'PROCESS_KILLED' or
                run_state_name == 'FAILED_EXECUTION')

    def can_rerun(self):
        run_state_name = self.run_state.name
        return (run_state_name == 'PENDING' or
                run_state_name == 'FAILED' or
                run_state_name == 'SUCCESS' or
                run_state_name == 'PROCESS_KILLED' or
                run_state_name == 'FAILED_EXECUTION')

    def get_color_class(self):
        color = 'color_' + self.run_state.name.lower()

        return color

    def clear_error_message(self):
        self.error_message = None
        self.save()

    def get_strategy(self):
        return self.job.get_strategy()

    def fail_task(self):
        strategy = self.get_strategy()
        strategy.fail_task(self)

    def finish_task(self):
        strategy = self.get_strategy()
        strategy.finish_task(self)

    def get_max_retries(self):
        return self.job.workflow_node.max_retries

    def rerun(self):
        if self.can_rerun and self.retry_count < self.get_max_retries():
            self.run_task()

    def increment_retry_count(self):
        self.retry_count = self.retry_count + ONE
        self.save()

    def reset_retry_count(self):
        self.retry_count = ZERO
        self.save()

    def run_task(self):
        self.increment_retry_count()
        self.set_start_run_time()
        strategy = self.get_strategy()
        _model_logger.info("Running task with strategy %s" % (str(strategy)))
        strategy.run_task(self)

    def set_pending_state(self):
        self.run_state = RunState.get_pending_state()
        self.save()

    def set_process_killed_state(self):
        self.run_state = RunState.get_process_killed_state()
        self.save()

    def set_running_state(self):
        self.run_state = RunState.get_running_state()
        self.save()

    def set_finished_execution_state(self):
        self.run_state = RunState.get_finished_execution_state()
        self.save()

    def set_failed_state(self):
        self.run_state = RunState.get_failed_state()
        self.save()

    def set_failed_execution_state(self):
        self.run_state = RunState.get_failed_execution_state()
        self.save()

    def set_success_state(self):
        self.run_state = RunState.get_success_state()
        self.save()

    def set_queued_state(self):
        self.run_state = RunState.get_queued_state()
        self.save()

    def in_success_state(self):
        return (self.run_state.name == RunState.get_success_state().name)

    def get_enqueued_job_object(self):
        return self.job.get_enqueued_object()

    def get_job_queue(self):
        return self.job.workflow_node.job_queue

    def get_executable(self):
        return self.get_job_queue().executable

    def get_task_name(self):
        return ('task_' + str(self.id))

    def get_umask(self):
        return '022'

    def get_pbs_commands(self):
        executable = self.get_executable()

        commands = []
        commands.append('#!/bin/bash')
        commands.append('#PBS -q ' + executable.pbs_queue)
        commands.append('#PBS -l ' + executable.pbs_processor)
        commands.append('#PBS -l ' + executable.pbs_walltime)
        commands.append('#PBS -N ' + self.get_task_name())
        commands.append('#PBS -V') # Import system variables
        commands.append('#PBS -r n') # Not re-runable
        commands.append('#PBS -j oe') # Join error and output streams
        commands.append('#PBS -o ' + self.log_file)
        commands.append(self.full_executable)
        commands.append('rtn_code=$?')
        commands.append('/shared/utils.x86_64/python-2.7/bin/python ' + settings.PBS_FINISH_PATH + ' $rtn_code ' + str(self.id))

        return commands

    def create_pbs_file(self, pbs_file):
        commands = self.get_pbs_commands()

        file_handle = open(pbs_file, 'w')
        for command in commands:
            file_handle.write(command + '\n')

        file_handle.close()

        self.pbs_file = pbs_file
        self.save()

    def get_enqueued_object(self):
        _model_logger.info('Task.get_enqueued_object')
        if self.enqueued_task_object_class == None:
            _model_logger.info('enqueued_task_object_class is nil for task')
            raise Exception('enqueued_task_object_class is nil for task: ' + str(self.id))

        if self.enqueued_task_object_id == None:
            _model_logger.info('enqueued_task_object_id is nil for task')
            raise Exception('enqueued_task_object_id is nil for task: ' + str(self.id))

        _model_logger.info('task enqueued object class: %s' % (self.enqueued_task_object_class))
        enqueued_object_class = import_class(self.enqueued_task_object_class)
        enqueued_object = enqueued_object_class.objects.get(id=self.enqueued_task_object_id)

        if enqueued_object == None:
            _model_logger.info('enqueued_object is None')
            msg = \
                'enqueued_object does not exist for enqueued_object_class of ' + \
                str(self.enqueued_task_object_class) + \
                ' and id of ' + \
                str(self.enqueued_task_object_id)
            _model_logger.info(msg)   
            raise Exception(msg)  
        
        _model_logger.info('task enqueued object: %s' % (enqueued_object))

        return enqueued_object

    def get_file_records(self):
        results = []
        file_records = FileRecord.objects.filter(task=self)
        for file_record in file_records:
            results.append(file_record.get_full_name())

        return results
