# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2017-2018. Allen Institute. All rights reserved.
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
from django.contrib.contenttypes.fields import GenericRelation
_model_logger = logging.getLogger('workflow_engine.models')


class WorkflowNode(models.Model):
    job_queue = models.ForeignKey(
        'workflow_engine.JobQueue')
    parent = models.ForeignKey(
        'workflow_engine.WorkflowNode', null=True, blank=True)
    is_head = models.BooleanField(default=False)
    workflow = models.ForeignKey(
        'workflow_engine.Workflow')
    disabled = models.BooleanField(default=False)
    batch_size = models.IntegerField(default=50)
    priority = models.IntegerField(default=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived = models.NullBooleanField(default=False)
    overwrite_previous_job = models.BooleanField(default=True)
    max_retries = models.IntegerField(default=3)
    configurations = GenericRelation('workflow_engine.Configuration')

    def __str__(self):
        return self.get_node_short_name()

    def get_node_short_name(self):
        return self.job_queue.name

    def get_node_name(self):
        return self.job_queue.name + '(' + str(self.get_total_number_of_jobs()) + ') ' + str(self.get_number_of_queued_and_running_jobs()) + ' / '+ str(self.batch_size)

    def get_workflow_name(self):
        return self.workflow.name

    def get_strategy(self):
        return self.job_queue.get_strategy()

    def get_children(self):
        return WorkflowNode.objects.filter(
            parent=self,
            archived=False)

    def get_total_number_of_jobs(self):
        return Job.objects.filter(
            workflow_node=self,
            archived=False).count()

    def get_number_of_queued_and_running_jobs(self):
        return len(self.get_queued_and_running_jobs())

    def get_queued_and_running_jobs(self):
        return Job.objects.filter(
            run_state_id__in=[
                RunState.get_queued_state().id,
                RunState.get_running_state().id],
            workflow_node=self,
            archived=False)

    def update(self,
               current_disabled,
               overwrite_previous_job,
               max_retries,
               batch_size,
               priority):
        prev_disabled = self.disabled

        self.disabled = current_disabled
        self.overwrite_previous_job = overwrite_previous_job,
        self.max_retries = int(max_retries)
        self.batch_size = int(batch_size)
        self.priority = int(priority)

        self.save()

        return prev_disabled

    def get_job_states(self):
        result = {}
        
        running_state = RunState.get_running_state()
        pending_state = RunState.get_pending_state()
        queued_state = RunState.get_queued_state()
        finished_execution_state = RunState.get_finished_execution_state()
        success_state = RunState.get_success_state()
        failed_execution_state = RunState.get_failed_execution_state()
        failed_state = RunState.get_failed_state()
        killed_state = RunState.get_process_killed_state()
    
        node_jobs = self.job_set.filter(archived=False)
    
        success_count = node_jobs.filter(
            run_state_id__in=[success_state.id]).count()

        failed_count = node_jobs.filter(
            run_state_id__in=[
                failed_execution_state.id,
                failed_state.id,
                killed_state.id]).count()
                
        running_count = node_jobs.filter(
            run_state_id__in=[
                running_state.id,
                pending_state.id,
                queued_state.id,
                finished_execution_state.id]).count()

        if success_count > 0:
            result[success_state.name] = success_count

        if failed_count > 0:
            result[failed_state.name] = failed_count

        if running_count > 0:
            result[running_state.name] = running_count

        return result

    def archive(self):
        self.archived = True
        self.save()


# circular imports
from workflow_engine.models.job import Job
from workflow_engine.models.run_state import RunState

