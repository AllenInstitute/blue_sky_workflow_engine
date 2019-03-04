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
import traceback
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import (
    IntegrityError,
    transaction
)
import logging
from workflow_engine.celery.signatures import (
    run_workflow_node_jobs_signature
)
from builtins import classmethod


class WorkflowController(object):
    _logger = logging.getLogger('workflow_engine.workflow_controller')

    @classmethod
    def run_workflow_nodes(cls, workflow_object):
        for workflow_node in WorkflowNode.objects.filter(
            workflow=workflow_object):
            if not workflow_node.disabled:
                run_workflow_node_jobs_signature.delay(workflow_node.id)

    @classmethod
    def run_workflow_node_jobs(cls, workflow_node):
        if (workflow_node.workflow.disabled or
            workflow_node.disabled):
            return

        number_of_queued_and_running_jobs = \
            workflow_node.get_number_of_queued_and_running_jobs()

        number_jobs_to_run = (
            workflow_node.batch_size - 
            number_of_queued_and_running_jobs
        )

        # run more jobs
        if number_jobs_to_run > ZERO:
            for job_to_run in workflow_node.get_n_pending_jobs(
                number_jobs_to_run):
                WorkflowController.job_run(job_to_run)

    # TODO: this is the signal from an out-of-band job
    @classmethod
    def set_jobs_for_run(cls, queue_name):
        '''Use workflow node or job queue name to run jobs.
        Useful for triggering wait strategy job queues.

        Parameters
        ----------
        wait_queue_name : String
            human readable name to look up the associated jobs
        '''
        jobs = Job.objects.filter(
            workflow_node__job_queue__name=queue_name,
            run_state__in=[
                RunState.get_pending_state(),
                RunState.get_queued_state()],
            archived=False)

        for job in jobs:
            job.set_pending_state()
            run_workflow_node_jobs_signature.delay(job.workflow_node.id)

    @classmethod
    def enqueue_next_queue_by_job_id(cls, job_id):
        job = Job.objects.get(id=job_id)
        WorkflowController.enqueue_next_queue(job)

    @classmethod
    def enqueue_next_queue(cls, source_job):
        source_node = source_job.workflow_node

        # TODO: factor out this loop body
        for node in source_node.get_children():
            strategy = node.get_strategy()
            enqueued_objects = strategy.get_objects_for_queue(source_job)

            for enqueued_object in enqueued_objects:
                if strategy.can_transition(enqueued_object, source_node):
                    WorkflowController.start_workflow_helper(
                        node,
                        enqueued_object,
                        node.overwrite_previous_job)

    @classmethod
    def set_job_for_run_if_valid(cls, job):
        if job.can_rerun():
            WorkflowController.set_job_for_run(job)

    @classmethod
    def set_job_for_run(cls, job):
        WorkflowController._logger.info('set for run')
        job.set_pending_state()
        run_workflow_node_jobs_signature.delay(job.workflow_node.id)

    @classmethod
    def set_jobs_for_run_by_id(cls, job_ids):
        records = Job.objects.filter(id__in=job_ids)

        for job_object in records:
            WorkflowController.set_job_for_run_if_valid(job_object)

    @classmethod
    def kill_job(cls, job_id):
        try:
            job = Job.objects.get(id=job_id)
            job.kill()
            run_workflow_node_jobs_signature.delay(job.workflow_node.id)
        except ObjectDoesNotExist:
            WorkflowController._logger.warning(
                'Tried to kill job %d which does not exist',
                job_id)

    @classmethod
    def create_tasks(cls, job):
        #reused_tasks = {}
        strategy = job.get_strategy()
        pending_state = RunState.get_pending_state()

        task_objects = strategy.get_task_objects_for_queue(
            job.enqueued_object
        )

        for task_object in task_objects:
            # TODO: deprecate
            enqueued_object_full_class = \
                type(task_object).__module__ + '.' + type(task_object).__name__

            default_options = {
                'run_state': pending_state,
                'archived': False,
                'retry_count': ZERO
            }

            enqueued_task_object_type = ContentType.objects.get_for_model(
                task_object
            )

            with transaction.atomic():
                try:
                    tsk, created = Task.objects.get_or_create(
                        enqueued_task_object_type=enqueued_task_object_type,
                        enqueued_task_object_id=task_object.id,
                        enqueued_task_object_class=enqueued_object_full_class, # TODO: deprecate
                        job=job,
                        defaults=default_options
                    )

                    if not created:
                        tsk.run_state=pending_state
                        tsk.archived=False
                        tsk.retry_count=0
                        tsk.save()
                except Exception as e:
                    raise(e)

            WorkflowController._logger.info(
                'creating task with enqueued type: {}'.format( 
                    enqueued_task_object_type
                )
            )

    @classmethod
    def job_run(cls, job):
        WorkflowController._logger.info('run')
        try:
            job.set_queued_state()

            job.set_start_run_time()
            job.clear_error_message()

            job.prep_job()

            WorkflowController.create_tasks(job)

            # job.remove_tasks(reused_tasks)

            for task in job.get_tasks():
                task.run_task()

        except Exception as e:
            job.set_error_message(
                str(e) + ' - ' + str(traceback.format_exc()), None)
            WorkflowController._logger.info(
                "Job exception: %s" % (job.error_message))
            job.set_failed_state()
            run_workflow_node_jobs_signature.delay(job.workflow_node.id)

    @classmethod
    def find_workflow_node(
        cls,
        workflow_name,
        start_node_name=None):
        workflow = Workflow.objects.get(
            name=workflow_name,
            archived=False)
        WorkflowController._logger.info(
            "starting %s at %s" % (
                workflow_name, str(start_node_name)))

        if start_node_name is not None:
            workflow_nodes = WorkflowNode.objects.filter(
                workflow=workflow,
                job_queue__name=start_node_name)
        else:
            workflow_nodes = WorkflowNode.objects.filter(
                workflow=workflow, sources=None)

        if len(workflow_nodes) != ONE:
            raise Exception(
                'Expected to find a single head workflow node but found: ' + \
                str(len(workflow_nodes)) + ': ' + \
                    ', '.join(str(wn) for wn in workflow_nodes))

        workflow_node = workflow_nodes[ZERO]

        return workflow_node

    @classmethod
    def enqueue_next_queue_by_workflow_node(
        cls,
        workflow_name,
        enqueued_object,
        start_node_name=None,
        set_success=True):
        workflow_node = cls.find_workflow_node(
            workflow_name,
            start_node_name)

        job = workflow_node.job_set.get(
            enqueued_object=enqueued_object,
            archived=False)

        if set_success:
            job.run_state = RunState.get_success_state()
            job.save()
        cls.enqueue_next_queue(job)

    @classmethod
    def enqueue_object(
        cls,
        workflow_node,
        enqueued_object,
        priority=None,
        reuse_job=False):
        if priority is None:
            priority = workflow_node.priority

        if reuse_job:
            default_options = {
                'run_state': RunState.get_pending_state(),
                'priority': priority
            }

            enqueued_object_type = ContentType.objects.get_for_model(
                enqueued_object
            )

            job, _ = Job.objects.update_or_create(
                enqueued_object_type=enqueued_object_type,
                enqueued_object_id=enqueued_object.id,
                workflow_node=workflow_node,
                defaults=default_options)
        else:
            job = Job()
            job.enqueued_object = enqueued_object
            job.workflow_node = workflow_node
            job.run_state = RunState.get_pending_state()
            job.priority = workflow_node.priority
            job.save()

        return job

    @classmethod
    def start_workflow_helper(
        cls,
        workflow_node,
        enqueued_object,
        reuse_job=False,
        raise_priority=False):
        if raise_priority:
            priority = workflow_node.priority - 10
        else:
            priority = workflow_node.priority

        job = WorkflowController.enqueue_object(
            workflow_node,
            enqueued_object,
            priority,
            reuse_job
        )

        WorkflowController._logger.info(
            "Start workflow job state: %s" % (str(job.run_state)))

        run_workflow_node_jobs_signature.delay(job.workflow_node.id)

    @classmethod
    def start_workflow(
        cls,
        workflow_name,
        enqueued_object,
        start_node_name=None,
        reuse_job=False,
        raise_priority=False):
        workflow_node = cls.find_workflow_node(
            workflow_name,
            start_node_name)

        WorkflowController.start_workflow_helper(
            workflow_node,
            enqueued_object,
            reuse_job,
            raise_priority
        )

    @classmethod
    def create_job(
        cls,
        workflow_node_id,
        enqueued_object_id,
        priority):
        workflow_node = WorkflowNode.objects.get(
            id=workflow_node_id)
        enqueued_object_type = workflow_node.job_queue.enqueued_object_type
        enqueued_object = enqueued_object_type.get_object_for_this_type(
            pk=enqueued_object_id)

        return WorkflowController.start_workflow_helper(
            workflow_node,
            enqueued_object,
            workflow_node.overwrite_previous_job,
            priority)

    @classmethod
    def get_enqueued_object(cls, task):
        return task.enqueued_task_object


# circular imports
from workflow_engine.models import (
    ZERO,
    ONE,
    Job,
    Task,
    RunState,
    WorkflowNode,
    Workflow
)

