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
from workflow_engine.mixins import Archivable, Runnable, Tagable, Timestamped
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import logging


_logger = logging.getLogger('workflow_engine.models.job')


class Job(Archivable, Runnable, Tagable, Timestamped, models.Model):
    enqueued_object_type = models.ForeignKey(
        ContentType,
        default=None,
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    '''Generic relation type'''

    enqueued_object_id = models.IntegerField(
        null=True,
        blank=True
    )
    '''Generic relation id'''

    enqueued_object = GenericForeignKey(
        'enqueued_object_type',
        'enqueued_object_id'
    )
    '''Combined generic relation type and id'''

    workflow_node = models.ForeignKey(
        'workflow_engine.WorkflowNode',
        on_delete=models.CASCADE
    )

    priority = models.IntegerField(
        default=50
    )

    def __str__(self):
        try:
            return "{} {} job {}".format(
                str(self.workflow_node),
                str(self.enqueued_object),
                self.pk
            )
        except:
            return "job {}".format(self.pk)

    def get_enqueued_object_display(self):
        result = None
        try:
            result = str(self.enqueued_object)
        except:
            result = 'None'

        return result

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
        has_failed = False
        tasks = self.get_tasks()
        for task in tasks:
            if task.in_failed_state():
                has_failed = True

        return has_failed

    def get_strategy(self):
        return self.workflow_node.get_strategy()

    # TODO: deprecate/remove - reuse tasks doesn't do this anymore
    def remove_tasks(self, resused_tasks):
        # strategy = self.get_strategy()
        for task in self.get_tasks():
            if task.id not in resused_tasks:
                task.archived = False
                task.save()

    # TODO: deprecate
    def get_tasks(self):
        return self.task_set.all()

    # TODO: deprecate
    def tasks(self):
        return self.task_set.all()

    def task_ids(self):
        return [t.id for t in self.tasks()]

    def number_of_tasks(self):
        return self.get_tasks().count()

    def prep_job(self):
        strategy = self.get_strategy()
        _logger.info("got strategy: " + str(strategy))
        strategy.prep_job(self)

    def all_tasks_finished(self):
        '''Check if all tasks have finished.
        '''
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
