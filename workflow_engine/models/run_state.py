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

    @staticmethod
    def is_failed_type_state(job_state_name):
        return (
            job_state_name == RunState.get_failed_execution_state().name or
            job_state_name == RunState.get_failed_state().name or
            job_state_name == RunState.get_process_killed_state().name)

    def is_running_type_state(job_state_name):
        return (
            job_state_name == RunState.get_pending_state().name or
            job_state_name == RunState.get_running_state().name or
            job_state_name == RunState.get_queued_state().name or
            job_state_name == RunState.get_finished_execution_state().name)

    @staticmethod
    def get_pending_state():
        return RunState.objects.get(name='PENDING')

    @staticmethod
    def get_running_state():
        return RunState.objects.get(name='RUNNING')

    @staticmethod
    def get_finished_execution_state():
        return RunState.objects.get(name='FINISHED_EXECUTION')

    @staticmethod
    def get_failed_execution_state():
        return RunState.objects.get(name='FAILED_EXECUTION')

    @staticmethod
    def get_failed_state():
        return RunState.objects.get(name='FAILED')

    @staticmethod
    def get_success_state():
        return RunState.objects.get(name='SUCCESS')

    @staticmethod
    def get_queued_state():
        return RunState.objects.get(name='QUEUED')

    @staticmethod
    def get_process_killed_state():
        return RunState.objects.get(name='PROCESS_KILLED')
