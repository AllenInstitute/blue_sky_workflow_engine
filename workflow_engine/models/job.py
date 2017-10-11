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
from .workflow_node import WorkflowNode
from .run_state import RunState
from .import_class import import_class
from . import TWO, ONE, ZERO, SECONDS_IN_MIN
import traceback
import logging
_model_logger = logging.getLogger('workflow_engine.models')


class Job(models.Model):
    enqueued_object_id = models.IntegerField()
    workflow_node = models.ForeignKey(WorkflowNode)
    run_state = models.ForeignKey(RunState)
    duration = models.DurationField(null=True)
    start_run_time = models.DateTimeField(null=True)
    end_run_time = models.DateTimeField(null=True)
    error_message = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    priority = models.IntegerField(default=50)
    archived = models.NullBooleanField(default=False)
    tags = models.CharField(max_length=255, null=True)

    def archive_record(self):
        for task in self.get_tasks():
            task.archive_record()

        self.archived = True
        self.save()

    def get_created_at(self):
        return timezone.localtime(self.created_at).strftime('%m/%d/%Y %I:%M:%S')

    def get_updated_at(self):
        return timezone.localtime(self.updated_at).strftime('%m/%d/%Y %I:%M:%S')

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
            result = None

        return result

    def get_enqueued_object_class_type(self):
        return self.workflow_node.job_queue.enqueued_object_class

    def set_error_message(self, error_message, task):

        if not task:
            self.error_message = 'job failed: ' + error_message
        elif error_message != None:
            self.error_message = 'task with id of ' + str(task.id) + ' failed: '  + error_message
        else:
            self.error_message = 'task with id of ' + str(task.id) + ' failed'

        self.save()

    def clear_error_message(self):
        self.error_message = None
        self.save()

    def has_failed_tasks(self):
        has_failed = False
        tasks = self.get_tasks()
        for task in tasks:
            if task.in_failed_state():
                has_failed = True

        return has_failed

    def can_rerun(self):
        run_state_name = self.run_state.name
        return (run_state_name == 'PENDING' or
                run_state_name == 'FAILED' or
                run_state_name == 'SUCCESS' or
                run_state_name == 'PROCESS_KILLED' or
                run_state_name == 'FAILED_EXECUTION')

    def set_pending_state(self):
        self.run_state = RunState.get_pending_state()
        self.save()

    def set_failed_state(self):
        self.run_state = RunState.get_failed_state()
        self.save()
        self.run_jobs()

    def set_failed_execution_state(self):
        self.run_state = RunState.get_failed_execution_state()
        self.save()
        self.run_jobs()

    def set_running_state_from_queued_or_pending(self):
        if(self.run_state.name == 'QUEUED' or self.run_state.name == 'PENDING'):
            self.set_running_state()

    def set_running_state(self):
        self.run_state = RunState.get_running_state()
        self.save()

    def set_success_state(self):
        self.run_state = RunState.get_success_state()
        self.save()
        self.run_jobs()

    def set_process_killed_state(self):
        self.run_state = RunState.get_process_killed_state()
        self.save()
        self.run_jobs()

    def get_enqueued_object(self):
        _model_logger.info(
            "importing %s" % (
                self.workflow_node.job_queue.enqueued_object_class)) 

        claz = import_class(self.workflow_node.job_queue.enqueued_object_class)
        enqueued_object = claz.objects.get(id=self.enqueued_object_id)

        return enqueued_object
    

    def get_strategy(self):
        return self.workflow_node.get_strategy()

    def archive_record(self):
        self.archived = True
        self.save()

    def remove_tasks(self, resused_tasks):
        strategy = self.get_strategy()
        for task in self.get_tasks():
            if task.id not in resused_tasks:
                task.archived = False
                task.save()

    def create_tasks(self):
        reused_tasks = {}
        strategy = self.get_strategy()
        pending_state = RunState.get_pending_state()

        task_objects = \
            strategy.get_task_objects_for_queue(
                self.get_enqueued_object())

        for task_object in task_objects:
            enqueued_object_full_class = \
                type(task_object).__module__ + '.' + type(task_object).__name__
        
            if self.workflow_node.overwrite_previous_job:
                try:
                    _model_logger.info(
                        'overwriting task with enqueued class: %s' %
                        (enqueued_object_full_class))
                    task = Task.objects.get(
                        enqueued_task_object_id=task_object.id,
                        enqueued_task_object_class=enqueued_object_full_class,
                        job=self)
                    task.run_state = pending_state
                    task.archived = False
                    task.retry_count = ZERO
                    task.save()
                except:
                    _model_logger.info(
                        'creating task with enqueued class: %s' %
                        (enqueued_object_full_class))
                    task = Task(
                        enqueued_task_object_id=task_object.id,
                        enqueued_task_object_class=enqueued_object_full_class,
                        run_state=pending_state,
                        job=self)
                    task.save()
            else:
                _model_logger.info(
                    'creating task with enqueued class: %s' %
                    (enqueued_object_full_class))
                task = Task(
                    enqueued_task_object_id=task_object.id,
                    enqueued_task_object_class=enqueued_object_full_class,
                    run_state=pending_state, job=self)
                task.save()

            reused_tasks[task.id] = True

        return reused_tasks

    def get_tasks(self):
        return Task.objects.filter(job_id=self.id, archived=False)

    def number_of_tasks(self):
        return len(self.get_tasks())

    def set_for_run_if_valid(self):
        if self.can_rerun():
            self.set_for_run()

    def set_for_run(self):
        self.set_pending_state()
        self.run_jobs()

    def prep_job(self):
        strategy = self.get_strategy()
        _model_logger.info("got strategy: " + str(strategy))
        strategy.prep_job(self)

    def run(self):
        try:
            self.set_queued_state()

            self.set_start_run_time()
            self.clear_error_message()

            self.prep_job()

            resused_tasks = self.create_tasks()

            self.remove_tasks(resused_tasks)

            for task in self.get_tasks():
                task.run_task()

        except Exception as e:
            self.set_error_message(str(e) + ' - ' + str(traceback.format_exc()), None)
            _model_logger.info("Job exception: %s" % (self.error_message))
            self.set_failed_state()

    def run_jobs(self):
        self.workflow_node.run_workflow_node_jobs()

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

    def enqueue_next_queue(self):
        children = self.workflow_node.get_children()
        for child in children:
            strategy = child.get_strategy()
            enqueued_objects = strategy.get_objects_for_queue(self)
            for enqueued_object in enqueued_objects:
                if strategy.can_transition(enqueued_object):
                    #try to get the job
                    jobs = Job.objects.filter(enqueued_object_id=enqueued_object.id,
                                              workflow_node_id=child.id,
                                              archived=False)

                    if len(jobs) > ZERO:
                        index = ZERO
                        for job in jobs:
                            #reset job if needed
                            if index == ZERO:
                                job.run_state = RunState.get_pending_state()
                                job.priority = child.priority
                                job.archived = False
                                job.save()
                                job.set_for_run()
                                
                            #should not have more than one job but just in case
                            else:
                                job.archived = True
                                job.save()

                            index += ONE
                    else:
                        #create the job if needed
                        job = Job(enqueued_object_id=enqueued_object.id,
                                  workflow_node=child,
                                  run_state=RunState.get_pending_state(),
                                  priority=child.priority)
                        job.save()
                        job.set_for_run()


    #check if all tasks have finished
    def all_tasks_finished(self):
        all_finished = True

        for task in self.get_tasks():
            if all_finished:
                all_finished = task.in_success_state()

        return all_finished

    def kill_tasks(self):
        for task in self.get_tasks():
            task.kill_task()

# circular imports
from .task import Task
