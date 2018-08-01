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
from workflow_engine.import_class import import_class
from django.core.exceptions import ObjectDoesNotExist
import logging
from workflow_engine.celery.signatures import run_workflow_node_jobs_signature


class WorkflowController(object):
    _logger = logging.getLogger('workflow_engine.workflow_controller')

    @classmethod
    def create_job(cls, workflow_node_id,
                   enqueued_object_id, priority):
        try:
            workflow_node = WorkflowNode.objects.get(
                id=workflow_node_id)
            job = Job.enqueue_object(
                workflow_node,
                enqueued_object_id,
                priority)
            run_workflow_node_jobs_signature.delay(job.workflow_node.id)

            return job
        except Exception as e:
            WorkflowController._logger.error(
                'Something went wrong running jobs: ' + str(e) + "\n" + \
                traceback.format_exc())
            raise e

    @classmethod
    def run_workflow_nodes(cls, workflow_object):
        for workflow_node in WorkflowNode.objects.filter(
            workflow=workflow_object):
            if not workflow_node.disabled:
                run_workflow_node_jobs_signature.delay(workflow_node.id)

    @classmethod
    def run_workflow_node_jobs(cls, workflow_node):
        try:
            if not workflow_node.workflow.disabled and not workflow_node.disabled:
                WorkflowController._logger.info(
                    "running job in workflow %s:%s" % (
                        str(workflow_node.workflow),
                        str(workflow_node.job_queue.name)))
                #check if more jobs can be run
                batch_size = workflow_node.batch_size

                try:
                    number_of_queued_and_running_jobs = \
                        workflow_node.get_number_of_queued_and_running_jobs()
                except Exception as e:
                    number_of_queued_and_running_jobs = ZERO

                number_jobs_to_run = \
                    batch_size - number_of_queued_and_running_jobs

                WorkflowController._logger.info(
                    ("%d jobs to be run. %d queued and running, "
                     "batch size %d in workflow %s:%s") % (
                        number_jobs_to_run,
                        number_of_queued_and_running_jobs,
                        batch_size,
                        str(workflow_node.workflow),
                        str(workflow_node.job_queue.name)))

                #run more jobs
                if number_jobs_to_run > ZERO:
                    try:
                        pending_jobs = \
                            Job.objects.filter(
                                run_state_id=RunState.get_pending_state().id,
                                workflow_node=workflow_node,
                                archived=False).order_by('priority',
                                                         '-updated_at')
                        WorkflowController._logger.info(
                            'pending jobs: %d' % (len(pending_jobs)))
                    except Exception as e:
                        WorkflowController._logger.info(
                            'pending jobs exception: %s' % (str(e)))
                        pending_jobs = []

                    for i in range(number_jobs_to_run):
                        if i < len(pending_jobs):
                            job = pending_jobs[i]
                            WorkflowController.job_run(job)
            else:
                WorkflowController._logger.info(
                    "not running jobs in disabled workflow %s" % (
                        str(workflow_node.workflow)))

        except Exception as e:
            WorkflowController._logger.error(
                'Something went wrong running jobs: ' + str(e) + "\n" + \
                traceback.format_exc())


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
    def enqueue_next_queue(cls, job):
        WorkflowController._logger.info('enqueue_next_queue')
        children = job.workflow_node.get_children()

        parent_enqueued_object = job.enqueued_object

        for child in children:
            strategy = child.get_strategy()
            child_enqueued_objects = strategy.get_objects_for_queue(
                job)

            for enqueued_object in child_enqueued_objects:
                if strategy.can_transition(enqueued_object):
                    #try to get the job
                    jobs = Job.objects.filter(
                        enqueued_object_id=enqueued_object.id,
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
                                WorkflowController.set_job_for_run(job)
                                
                            #should not have more than one job but just in case
                            else:
                                job.archived = True
                                job.save()

                            index += ONE
                    else:
                        # create the job if needed
                        job = Job(enqueued_object=enqueued_object,
                                  workflow_node=child,
                                  run_state=RunState.get_pending_state(),
                                  priority=child.priority)
                        job.save()
                        
                        WorkflowController.set_job_for_run(job)

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
        reused_tasks = {}
        strategy = job.get_strategy()
        pending_state = RunState.get_pending_state()

        task_objects = \
            strategy.get_task_objects_for_queue(job.enqueued_object)

        for task_object in task_objects:
            enqueued_object_full_class = \
                type(task_object).__module__ + '.' + type(task_object).__name__

            if job.workflow_node.overwrite_previous_job:
                try:
                    task = Task.objects.get(
                        enqueued_task_object_id=task_object.id,
                        enqueued_task_object_class=enqueued_object_full_class,
                        job=job)
                    task.run_state = pending_state
                    task.archived = False
                    task.retry_count = ZERO
                    task.save()
                except:
                    task = Task(
                        enqueued_task_object=task_object,
                        enqueued_task_object_class=enqueued_object_full_class,
                        run_state=pending_state,
                        job=job)
                    task.save()
            else:
                WorkflowController._logger.info(
                    'creating task with enqueued class: %s' %
                    (enqueued_object_full_class))
                task = Task(
                    enqueued_task_object=task_object,
                    enqueued_task_object_class=enqueued_object_full_class,
                    run_state=pending_state, job=job)
                task.save()

            reused_tasks[task.id] = True

        return reused_tasks

    # TODO: combine w/ job.enqueue_object
    @classmethod
    def enqueue_object(cls, workflow_node, enqueued_object):
        job = Job()
        job.workflow_node = workflow_node
        job.enqueued_object = enqueued_object
        job.run_state = RunState.get_pending_state()
        job.priority = job.workflow_node.priority
        job.save()

    @classmethod
    def job_run(cls, job):
        WorkflowController._logger.info('run')
        try:
            job.set_queued_state()

            job.set_start_run_time()
            job.clear_error_message()

            job.prep_job()

            reused_tasks = WorkflowController.create_tasks(job)

            job.remove_tasks(reused_tasks)

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
    def start_workflow(cls,
                       workflow_name,
                       enqueued_object,
                       start_node_name=None):
        workflow = Workflow.objects.get(name=workflow_name)
        WorkflowController._logger.info(
            "starting %s at %s" % (
                workflow_name, str(start_node_name)))

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
        job.enqueued_object=enqueued_object
        job.workflow_node=workflow_node
        job.run_state=RunState.get_pending_state()
        job.priority = workflow_node.priority
        job.save()

        WorkflowController._logger.info("Start workflow job state: %s" % (str(job.run_state)))

        run_workflow_node_jobs_signature.delay(job.workflow_node.id)

    @classmethod
    def start_workflow_2(
        cls,
        workflow_name,
        enqueued_object,
        start_node_name=None,
        reuse_job=False,
        raise_priority=False):
        workflow = Workflow.objects.get(name=workflow_name)
        WorkflowController._logger.info(
            "starting %s at %s" % (
                workflow_name, str(start_node_name)))

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

        if raise_priority:
            priority = workflow_node.priority - 10
        else:
            priority = workflow_node.priority

        if reuse_job:
            default_options = {
                'run_state': RunState.get_pending_state(),
                'priority': priority
            }
            job, _ = Job.objects.update_or_create(
                enqueued_object_id=enqueued_object.id,
                workflow_node=workflow_node,
                defaults=default_options)
        else:
            job = Job()
            job.enqueued_object=enqueued_object
            job.workflow_node=workflow_node
            job.run_state=RunState.get_pending_state()
            job.priority = workflow_node.priority
            job.save()

        WorkflowController._logger.info("Start workflow job state: %s" % (str(job.run_state)))

        run_workflow_node_jobs_signature.delay(job.workflow_node.id)

    @classmethod
    def get_enqueued_object(cls, task):
        return task.enqueued_task_object

    @classmethod
    def get_enqueued_object_deprecated(cls, task):
        WorkflowController._logger.info(
            'WorkflowController.get_enqueued_object')
        if task.enqueued_task_object_class == None:
            WorkflowController._logger.info(
                'enqueued_task_object_class is nil for task')
            raise Exception(
                'enqueued_task_object_class is nil for task: ' + str(task.id))

        if task.enqueued_task_object_id == None:
            WorkflowController._logger.info(
                'enqueued_task_object_id is nil for task')
            raise Exception(
                'enqueued_task_object_id is nil for task: ' + str(task.id))

        WorkflowController._logger.info(
            'task enqueued object class: %s' % (
                task.enqueued_task_object_class))
        enqueued_object_class = import_class(
            task.enqueued_task_object_class)
        enqueued_object = enqueued_object_class.objects.get(
            id=task.enqueued_task_object_id)

        if enqueued_object == None:
            WorkflowController._logger.info('enqueued_object is None')
            msg = \
                'enqueued_object does not exist for enqueued_object_class of ' + \
                str(task.enqueued_task_object_class) + \
                ' and id of ' + \
                str(task.enqueued_task_object_id)
            WorkflowController._logger.info(msg)
            raise Exception(msg)  
        
        WorkflowController._logger.info(
            'task enqueued object: %s' % (enqueued_object))

        return enqueued_object


# circular imports
from workflow_engine.models import ZERO, ONE
from workflow_engine.models.job import Job
from workflow_engine.models.task import Task
from workflow_engine.models.run_state import RunState
from workflow_engine.models.workflow_node import WorkflowNode
from workflow_engine.models.workflow import Workflow

