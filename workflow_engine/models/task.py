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
from workflow_engine.models import ONE, ZERO, TWO, SECONDS_IN_MIN
from workflow_client.pbs_utils import PbsUtils
import logging
import traceback
import os


_logger = logging.getLogger('workflow_engine.models.task')


class Task(models.Model):
    enqueued_task_object_id = models.IntegerField(null=True)
    enqueued_task_object_class = models.CharField(max_length=255, null=True)
    job = models.ForeignKey(
        'workflow_engine.Job')
    archived = models.NullBooleanField(default=False)
    run_state = models.ForeignKey(
        'workflow_engine.RunState')
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
        return "%s %s task %d" % (
            str(self.job.workflow_node),
            str(WorkflowController.get_enqueued_object(self)),
            self.id)
    def get_created_at(self):
        return timezone.localtime(self.created_at).strftime('%m/%d/%Y %I:%M:%S')

    def get_updated_at(self):
        return timezone.localtime(self.updated_at).strftime('%m/%d/%Y %I:%M:%S')

    def set_error_message(self, error_message):
        self.error_message = str(error_message)
        self.save()
        self.job.set_error_message(self.error_message, self)

    def set_pbs_id(self, pbs_id):
        self.pbs_id = pbs_id
        self.save()

    def environment_vars(self):
        '''
            returns: environment variable list in form VAR=val
        '''
        env = self.get_job_queue().executable.environment

        if env is None:
            return []

        return self.get_job_queue().executable.environment.split(';')

    def pbs_task(self):
        pbs_workflow = self.job.workflow_node.workflow.use_pbs
        pbs_executable = self.get_job_queue().executable.remote_queue == 'pbs'

        is_pbs = pbs_executable or pbs_workflow 
        _logger.info("pbs_task: %s" % (is_pbs))

        return is_pbs

    def kill_task(self):
        from celery.task.control import revoke
        self.set_process_killed_state()
        revoke(self.id, terminate=True)
        strategy = self.get_strategy()
        if strategy.is_execution_strategy():
            strategy.kill_pbs_task(self)

        self.set_end_run_time()

    def get_start_run_time(self):
        result = None
        if self.start_run_time != None:
            result = timezone.localtime(
                self.start_run_time).strftime('%m/%d/%Y %I:%M:%S')

        return result

    def get_end_run_time(self):
        result = None
        if self.end_run_time != None:
            result = timezone.localtime(
                self.end_run_time).strftime('%m/%d/%Y %I:%M:%S')

        return result

    def get_enqueued_object_display(self):
        result = None
        try:
            enqueued_object = WorkflowController.get_enqueued_object(self)
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
        self.duration = self.end_run_time - self.start_run_time
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

    def set_failed_execution_fields_and_rerun(self):
        self.set_failed_execution_state()
        self.set_end_run_time()
        self.job.set_failed_execution_state()
        self.job.set_end_run_time()
        self.rerun()

    def finish_task(self):
        try:
            self.set_finished_execution_state()
            self.set_success_state()
            self.set_end_run_time()
            self.job.set_success_state()
            self.job.set_end_run_time()
            WorkflowController.enqueue_next_queue(self.job)
        except Exception as e:
            mess = str(e) + ' - ' + str(traceback.format_exc())
            _logger.error(mess)
            self.set_error_message(mess)
            self.fail_task()


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
        _logger.info("Running task with strategy %s" % (str(strategy)))
        strategy.run_task(self)

    def set_pending_state(self):
        _logger.info("set pending state")
        strategy = self.get_strategy()
        strategy.run_task(self)
        self.run_state = RunState.get_pending_state()
        self.save()

    def set_process_killed_state(self):
        _logger.info("set process killed state")
        self.run_state = RunState.get_process_killed_state()
        self.save()

    def set_running_state(self):
        _logger.info("set running state")
        self.run_state = RunState.get_running_state()
        self.save()

    def set_finished_execution_state(self):
        _logger.info("finished execution state")
        self.run_state = RunState.get_finished_execution_state()
        self.save()

    def set_failed_state(self):
        _logger.info("set failed state")
        self.run_state = RunState.get_failed_state()
        self.save()

    def set_failed_execution_state(self):
        _logger.info("set failed execution state")
        self.run_state = RunState.get_failed_execution_state()
        self.save()

    def set_success_state(self):
        _logger.info("set success state")
        self.run_state = RunState.get_success_state()
        self.save()

    def set_queued_state(self):
        _logger.info("set queued state")
        self.run_state = RunState.get_queued_state()
        self.save()

    def in_pending_state(self):
        return (self.run_state.name == 'PENDING')

    def in_success_state(self):
        return (self.run_state.name == RunState.get_success_state().name)

    def get_enqueued_job_object(self):
        return self.job.get_enqueued_object()

    def get_job_queue(self):
        return self.job.workflow_node.job_queue

    def get_job(self):
        return self.job

    def get_executable(self):
        return self.get_job_queue().executable

    def get_task_name(self):
        return ('task_' + str(self.id))

    def get_umask(self):
        return '022'

    def get_pbs_commands(self):
        executable = self.get_executable()

        pbs_file_contents = PbsUtils().get_template(
            executable, self, settings)

        return pbs_file_contents

    def create_pbs_file(self, pbs_file):
        pbs_file_contents = self.get_pbs_commands()

        with open(pbs_file, 'w') as file_handle:
            file_handle.write(pbs_file_contents)
        os.chmod(pbs_file, 0o664)

        self.pbs_file = pbs_file
        self.save()

    def get_file_records(self):
        results = []
        file_records = FileRecord.objects.filter(task=self)
        for file_record in file_records:
            results.append(file_record.get_full_name())

        return results

# circular imports
from workflow_engine.models.run_state import RunState
from workflow_engine.models.file_record import FileRecord
from workflow_engine.workflow_controller import WorkflowController
