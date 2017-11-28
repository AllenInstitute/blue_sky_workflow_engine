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
import logging
_model_logger = logging.getLogger('workflow_engine.models')


class RunState(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    @classmethod
    def is_failed_type_state(cls, job_state_name):
        return (
            job_state_name == cls.get_failed_execution_state().name or
            job_state_name == cls.get_failed_state().name or
            job_state_name == cls.get_process_killed_state().name)

    # TODO: make class method
    @classmethod
    def is_running_type_state(cls, job_state_name):
        return (
            job_state_name == cls.get_pending_state().name or
            job_state_name == cls.get_running_state().name or
            job_state_name == cls.get_queued_state().name or
            job_state_name == cls.get_finished_execution_state().name)

    @classmethod
    def get_pending_state(cls):
        return cls.objects.get(name='PENDING')

    @classmethod
    def get_running_state(cls):
        return cls.objects.get(name='RUNNING')

    @classmethod
    def get_finished_execution_state(cls):
        return cls.objects.get(name='FINISHED_EXECUTION')

    @classmethod
    def get_failed_execution_state(cls):
        return cls.objects.get(name='FAILED_EXECUTION')

    @classmethod
    def get_failed_state(cls):
        return cls.objects.get(name='FAILED')

    @classmethod
    def get_success_state(cls):
        return cls.objects.get(name='SUCCESS')

    @classmethod
    def get_queued_state(cls):
        return cls.objects.get(name='QUEUED')

    @classmethod
    def get_process_killed_state(cls):
        return cls.objects.get(name='PROCESS_KILLED')
