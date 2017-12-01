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
from workflow_engine.models import ONE, ZERO
import logging
_model_logger = logging.getLogger('workflow_engine.models')


class Workflow(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True)
    ingest_strategy_class = models.CharField(max_length=255, null=True)
    disabled = models.BooleanField(default=False)
    use_pbs = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_head_workfow_nodes(self):
        return WorkflowNode.objects.filter(is_head=True, workflow=self.id)

    @classmethod
    def start_workflow(cls,
                       workflow_name,
                       enqueued_object,
                       start_node_name=None):
        workflow = Workflow.objects.get(name=workflow_name)
        _model_logger.info("starting %s" % (workflow_name))

        if start_node_name is not None:
            workflow_nodes = WorkflowNode.objects.filter(
                job_queue__name=start_node_name)
        else:
            workflow_nodes = WorkflowNode.objects.filter(
                workflow=workflow, parent=None)

        if len(workflow_nodes) != ONE:
            raise Exception(
                'Expected to find a single head workflow node but found: ' + \
                str(len(workflow_nodes)) + ': ' + \
                    ', '.join(str(wn) for wn in workflow_nodes))

        workflow_node = workflow_nodes[ZERO]

        job = Job()
        job.enqueued_object_id=enqueued_object.id
        job.workflow_node=workflow_node
        job.run_state=RunState.get_pending_state()
        job.priority = workflow_node.priority
        job.save()
        
        _model_logger.info("Start workflow job state: %s" % (str(job.run_state)))
        
        job.run_jobs()

# circular imports
from workflow_engine.models.workflow_node import WorkflowNode
from workflow_engine.models.job import Job
from workflow_engine.models.run_state import RunState
