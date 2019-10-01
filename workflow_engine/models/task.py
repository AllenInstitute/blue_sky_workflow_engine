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
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from workflow_engine.models import ONE, ZERO
from workflow_engine.mixins import Archivable, Runnable, Tagable, Timestamped
from workflow_client.pbs_utils import PbsUtils
import os
import logging


_logger = logging.getLogger('workflow_engine.models.task')


class Task(Archivable, Runnable, Tagable, Timestamped, models.Model):
    enqueued_task_object_type = models.ForeignKey(
        ContentType,
        default=None,
        null=True,
        on_delete=models.CASCADE
    )
    '''Generic relation type'''

    enqueued_task_object_id = models.IntegerField(
        null=True
    )
    '''Generic relation id'''

    enqueued_task_object = GenericForeignKey(
        'enqueued_task_object_type',
        'enqueued_task_object_id')
    '''Combined generic relation type and id'''

    job = models.ForeignKey(
        'workflow_engine.Job',
        on_delete=models.CASCADE
    )

    full_executable = models.CharField(
        max_length=1000,
        null=True
    )

    log_file = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    input_file = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    output_file = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    pbs_file = models.CharField(
        max_length=255,
        null=True,
        blank=True)

    pbs_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    retry_count = models.IntegerField(
        default=0
    )

    def __str__(self):
        try:
            return "{} {} task {}".format(
                str(self.job.workflow_node),
                str(self.enqueued_task_object),
                self.pk
            )
        except:
            return "task {}".format(self.pk)

    def set_error_message(self, error_message):
        self.error_message = str(error_message)
        self.save()
        self.job.set_error_message(self.error_message, self)

    def set_pbs_id(self, pbs_id):
        self.pbs_id = pbs_id
        _logger.info("Set PBS ID for task %d to %s", self.id, pbs_id)
        self.save()

    def environment_vars(self):
        '''
            returns: environment variable list in form VAR=val
        '''
        env = self.get_job_queue().executable.environment_vars()

        if env is None:
            return []

        return env

    def has_pbs_workflow(self):
        self.job.workflow_node.workflow.use_pbs

    def has_pbs_executable(self):
        return self.get_executable().remote_queue in ['pbs', 'spark_moab']

    def pbs_task(self):
        is_pbs = self.has_pbs_executable() or self.has_pbs_workflow() 

        return is_pbs

    def kill_task(self):
        self.set_process_killed_state()
        strategy = self.get_strategy()

        if strategy.is_execution_strategy():
            strategy.kill_pbs_task(self)

        self.set_end_run_time()

    def get_enqueued_object_display(self):
        result = None

        try:
            result = str(self.enqueued_task_object)
        except:
            result = str(None)

        return result

    def clear_error_message(self):
        self.error_message = None
        self.save()

    def get_strategy(self):
        return self.job.get_strategy()

    def get_task_arguments(self):
        return ' '.join(
            self.get_strategy().get_task_arguments(self)
        )

    def set_failed_fields_and_rerun(self, rerun=True):
        self.set_failed_state()
        self.set_end_run_time()
        self.job.set_failed_state()
        self.job.set_end_run_time()

        if rerun is True:
            self.rerun()

    def set_failed_execution_fields_and_rerun(self, rerun=True):
        self.set_failed_execution_state()
        self.set_end_run_time()
        self.job.set_failed_execution_state()
        self.job.set_end_run_time()

        if rerun is True:
            self.rerun()

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
        _logger.info(
            "Running task with strategy %s",
            str(strategy)
        )
        strategy.run_task(self)

    def get_enqueued_job_object(self):
        return self.job.enqueued_object

    def get_job_queue(self):
        return self.job.workflow_node.job_queue

    def get_job(self):
        return self.job

    def get_executable(self):
        return self.get_job_queue().executable

    def get_task_name(self):
        return ('task_' + str(self.id))

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
        return list(self.filerecord_set.all())
