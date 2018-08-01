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
from workflow_engine.import_class import import_class
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from workflow_engine.models import TWO, SECONDS_IN_MIN
import logging


_logger = logging.getLogger('workflow_engine.models.job')


class Job(models.Model):
    enqueued_object_type = models.ForeignKey(
        ContentType, default=None, null=True)
    enqueued_object_id = models.IntegerField(null=True)
    enqueued_object = GenericForeignKey(
        'enqueued_object_type',
        'enqueued_object_id')
    workflow_node = models.ForeignKey(
        'workflow_engine.WorkflowNode')
    run_state = models.ForeignKey(
        'workflow_engine.RunState')
    duration = models.DurationField(null=True)
    start_run_time = models.DateTimeField(null=True)
    end_run_time = models.DateTimeField(null=True)
    error_message = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    priority = models.IntegerField(default=50)
    archived = models.NullBooleanField(default=False)
    tags = models.CharField(max_length=255, null=True)

    def __str__(self):
        try:
            enqueued_object_name = str(self.get_enqueued_object())
        except:
            enqueued_object_name = "None"

        return "%s %s job %d" % (str(self.workflow_node),
                                 enqueued_object_name,
                                 self.id)

    def archive_record(self):
        self.archived = True
        self.save()

    def get_created_at(self):
        return timezone.localtime(self.created_at).strftime(
            '%m/%d/%Y %I:%M:%S')

    def get_updated_at(self):
        return timezone.localtime(self.updated_at).strftime(
            '%m/%d/%Y %I:%M:%S')

    def get_color_class(self):
        color = 'color_' + self.run_state.name.lower()

        return color

    def set_queued_state(self):
        self.run_state = RunState.get_queued_state()
        self.save()

    def get_enqueued_object_display(self):
        result = None
        try:
            enqueued_object = self.get_enqueued_object()
            result = str(enqueued_object)
        except:
            result = 'None'

        return result

    def get_enqueued_object_class_type(self):
        return self.workflow_node.job_queue.enqueued_object_class

    def set_error_message(self, error_message, task):
        if not task:
            self.error_message = 'job failed: ' + error_message
        elif error_message != None:
            self.error_message = \
                'task with id of ' + str(task.id) + \
                ' failed: '  + error_message
        else:
            self.error_message = 'task with id of ' + str(task.id) + ' failed'

        self.save()

    def clear_error_message(self):
        self.error_message = None
        self.save()

    def has_failed_tasks(self):
        _logger.info('has failed tasks')
        has_failed = False
        tasks = self.get_tasks()
        for task in tasks:
            if task.in_failed_state():
                has_failed = True

        return has_failed

    def can_rerun(self):
        _logger.info('can rerun')
        run_state_name = self.run_state.name
        return (run_state_name == 'PENDING' or
                run_state_name == 'FAILED' or
                run_state_name == 'SUCCESS' or
                run_state_name == 'PROCESS_KILLED' or
                run_state_name == 'FAILED_EXECUTION')

    def set_pending_state(self):
        _logger.info('set pending')
        self.run_state = RunState.get_pending_state()
        self.save()

    def set_failed_state(self):
        _logger.info('set failed')
        self.run_state = RunState.get_failed_state()
        self.save()


    def set_failed_execution_state(self):
        _logger.info('set failed execution')
        self.run_state = RunState.get_failed_execution_state()
        self.save()


    def set_running_state_from_queued_or_pending(self):
        if(self.run_state.name == 'QUEUED' or self.run_state.name == 'PENDING'):
            self.set_running_state()

    def set_running_state(self):
        _logger.info('set running')
        self.run_state = RunState.get_running_state()
        self.save()

    def set_success_state(self):
        _logger.info('set success')
        self.run_state = RunState.get_success_state()
        self.save()


    def set_process_killed_state(self):
        _logger.info('set process_killed')
        self.run_state = RunState.get_process_killed_state()
        self.save()

    @classmethod
    def enqueue_object(cls, workflow_node, enqueued_object_id, priority):
        enqueued_object_type = workflow_node.job_queue.enqueued_object_type
        job = Job()
        job.enqueued_object_type = enqueued_object_type
        job.enqueued_object_id = enqueued_object_id
        job.enqueued_object = \
            enqueued_object_type.get_object_for_this_type(
                pk=enqueued_object_id)
        job.workflow_node = workflow_node
        job.run_state = RunState.get_pending_state()
        job.priority = priority
        job.save()

        return job

    def get_enqueued_object(self):
        return self.enqueued_object

    def get_enqueued_object_deprecated(self):
        _logger.info(
            "importing %s" % (
                self.workflow_node.job_queue.enqueued_object_class)) 

        claz = import_class(
            self.workflow_node.job_queue.enqueued_object_class)
        enqueued_object = claz.objects.get(
            id=self.enqueued_object_id)
        return enqueued_object

    def get_strategy(self):
        return self.workflow_node.get_strategy()

    def remove_tasks(self, resused_tasks):
        # strategy = self.get_strategy()
        for task in self.get_tasks():
            if task.id not in resused_tasks:
                task.archived = False
                task.save()

    def get_tasks(self):
        return self.task_set.filter(archived=False)

    def tasks(self):
        return self.task_set.filter(archived=False)

    def task_ids(self):
        return [t.id for t in self.tasks()]

    def number_of_tasks(self):
        return len(self.get_tasks())

    def prep_job(self):
        strategy = self.get_strategy()
        _logger.info("got strategy: " + str(strategy))
        strategy.prep_job(self)

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

    # check if all tasks have finished
    def all_tasks_finished(self):
        _logger.info('check all tasks finished')
        all_finished = True

        for task in self.get_tasks():
            if all_finished:
                all_finished = task.in_success_state()

        return all_finished


    def kill(self):
        self.set_process_killed_state()
        self.kill_tasks()
        self.set_end_run_time()


    def kill_tasks(self):
        for task in self.get_tasks():
            task.kill_task()

    def workflow(self):
        return self.workflow_node.workflow.name

# circular imports
from workflow_engine.models.run_state import RunState
