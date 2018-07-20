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
from workflow_engine.strategies import base_strategy
from django.conf import settings
import os
import subprocess
import traceback
import logging
import simplejson as json
from workflow_engine.celery.signatures \
    import enqueue_next_queue_signature, cancel_task_signature
from workflow_engine.celery.result_tasks import process_pbs_id
from workflow_engine.celery.moab_tasks import submit_moab_task


class ExecutionStrategy(base_strategy.BaseStrategy):
    _log = logging.getLogger('workflow_engine.strategies.execution_strategy')
    # ## ## everthing bellow this can be overriden# ## ##

    # override if needed
    # get the data for the input file
    def get_input(self, enqueued_object, storage_directory, task):
        input_data = {}
        input_data['input'] = str(enqueued_object)

        return input_data

    def get_executable(self, task):
        return task.job.workflow_node.job_queue.executable

    def get_remote_queue(self, task):
        return self.get_executable(task).remote_queue

    # override if needed
    # return the full executable path with all arguments and parameters
    def get_full_executable(self, task):
        try:
            executable = self.get_executable(task)
            ExecutionStrategy._log.info(
                'executable %s' % (str(executable)))
        except Exception as e:
            raise Exception(
                'Could not find executable associated with task: ' + \
                str(task.id) + ' - ' + str(e))

        arguments = executable.static_arguments
        ExecutionStrategy._log.info('static arguments %s' % (str(arguments)))

        input_file = self.get_input_file(task)
        ExecutionStrategy._log.info('input file %s' % (str(input_file)))

        # populate the input file
        storage_dir = self.get_task_storage_directory(task)

        enqueued_object = WorkflowController.get_enqueued_object(task)
        
        ExecutionStrategy._log.info(
            'enqueued_object: %s',
            str(enqueued_object))
        
        self.create_input_file(input_file,
                               enqueued_object,
                               storage_dir,
                               task)

        output_file = self.get_output_file(task)

        task.input_file = input_file
        task.output_file = output_file
        task.tags = executable.version
        task.save()

        executable_elements = []
        if task.pbs_task() and executable.pbs_executable_path != None:
            executable_elements.append(executable.pbs_executable_path)
        else:
            executable_elements.append(executable.executable_path)

        if arguments != None:
            executable_elements.append(arguments)

        if input_file != None:
            executable_elements.append('--input_json')
            executable_elements.append(input_file)

        if output_file != None:
            executable_elements.append('--output_json')
            executable_elements.append(output_file)

        full_executable_string = ' '.join(executable_elements)

        ExecutionStrategy._log.info(
            'full executable string: %s',
            full_executable_string)

        return full_executable_string

    # override if needed
    def skip_execution(self, enqueued_object):
        return False

    # ## ## everthing bellow this should not be overriden# ## ##

    # Do not override
    def set_error_message_from_log(self, task):
        try:
            if os.path.isfile(task.log_file):
                result = subprocess.run(
                    ['tail', task.log_file], stdout=subprocess.PIPE)
                task.set_error_message(result.stdout.decode("utf-8"))
        except Exception as e:
            ExecutionStrategy._log.error('Something went wrong: ' + str(e))
            print('Something went wrong: ' + str(e)) # TODO: remove?

    # Do not override
    def fail_execution_task(self, task):
        try:
            self.set_error_message_from_log(task)
            self.on_failure(task)
        except Exception as e:
            err_msg = '%s - %s' % (
                str(e),
                str(traceback.format_exc()))
            ExecutionStrategy._log.info(err_msg)
            task.set_error_message(err_msg)

        task.set_failed_execution_fields_and_rerun()

    # Do not override
    def running_task(self, task):
        try:
            self.on_running(task)
            task.set_start_run_time()
            task.set_running_state()
            job = task.job
            if not job.has_failed_tasks():
                job.set_running_state()
        except Exception as e:
            task.set_error_message(
                str(e) + ' - ' + str(traceback.format_exc()))
            self.fail_task(task)

    # Do not override
    def finish_task(self, task):
        ExecutionStrategy._log.info('finish task')
        try:
            ExecutionStrategy._log.info('setting finished execution state')
            task.set_finished_execution_state()

            ExecutionStrategy._log.info('reading output')
            if self.is_execution_strategy():
                self.read_output(task)

            ExecutionStrategy._log.info('setting success state')
            task.set_success_state()
            task.set_end_run_time()

            ExecutionStrategy._log.info('checking tasks')
            if task.job.all_tasks_finished():
                task.job.set_success_state()
                task.job.set_end_run_time()
                enqueue_next_queue_signature.delay(task.job.id)

        except Exception as e:
            ExecutionStrategy._log.error(
                str(e) + ' - ' + str(traceback.format_exc()))

            task.set_error_message(
                str(e) + ' - ' + str(traceback.format_exc()))
            self.fail_task(task)

    # Do not override
    def run_task(self, task):
        try:
            self.prep_task(task)
            task.full_executable = self.get_full_executable(task)
            ExecutionStrategy._log.info(
                'executable: %s' % (str(task.full_executable)))
            task.log_file = self.get_log_file(task)
            task.pbs_id = None
            task.save()
            self.run_asynchronous_task(task)
        except Exception as e:
            ExecutionStrategy._log.error(e)
            task.set_error_message(
                str(e) + ' - ' + str(traceback.format_exc()))
            self.fail_task(task)

    # Do not override
    def add_write_to_log_command(self, executable, log_file):
        return str(executable) + ' > ' + str(log_file) + ' 2>&1'

    def kill_pbs_task(self, task):
        if task.pbs_id != None:
            cancel_task_signature.delay(True, task.pbs_id)

    # Do not override
    def run_asynchronous_task(self, task):
        task.clear_error_message()

        enqueued_object = WorkflowController.get_enqueued_object(task)

        if self.skip_execution(enqueued_object):
            # TODO: make this a "skip" remote queue
            ExecutionStrategy._log.info('skipping execution')
            self.running_task(task)
            self.finish_task(task)
        else:
            remote_queue = self.get_remote_queue(task)
            use_pbs = False
            if task.pbs_task():
                use_pbs = True
                ExecutionStrategy._log.info('pbs task')

                pbs_file = self.get_pbs_file(task)
                task.create_pbs_file(pbs_file)

                executable = 'qsub ' + pbs_file  # TODO deprecate
                queue_name = settings.MOAB_MESSAGE_QUEUE_NAME
            elif 'spark' == remote_queue:
                queue_name = settings.SPARK_MESSAGE_QUEUE_NAME
            else:
                queue_name = settings.MESSAGE_QUEUE_NAME
                executable = self.add_write_to_log_command(
                    task.full_executable, task.log_file)

            ExecutionStrategy._log.info(
                'apply async celery queue: %s' % (queue_name))
            set_moab_id = process_pbs_id.s(task.id).set(
                queue_name=settings.RESULT_MESSAGE_QUEUE_NAME)
            submit_moab_task.apply_async(
                (task.id,),
                queue=settings.MOAB_MESSAGE_QUEUE_NAME,
                link=[set_moab_id])

    # this method creates the input file
    # Do not override
    def create_input_file(self,
                          input_file,
                          enqueued_object,
                          storage_directory,
                          task):
        ExecutionStrategy._log.info("input data")

        input_data = self.get_input(enqueued_object, storage_directory, task)

        ExecutionStrategy._log.info(json.dumps(input_data))

        with open(input_file, 'w') as in_file:
            json.dump(input_data, in_file, indent=2)
        #os.chmod(input_file, 0o664)

    # Do not override
    # TODO: this seems too rigid
    def get_output_file(self, task):
        storage_directory = self.get_or_create_task_storage_directory(task)
        output_path = os.path.join(
            storage_directory,
            'output_' + str(task.id) + '.json')

        ExecutionStrategy._log.info("output_path: %s", output_path)

        return output_path

    # Do not override
    def get_pbs_file(self, task):
        storage_directory = self.get_or_create_task_storage_directory(task)
        return os.path.join(storage_directory, 'pbs_' + str(task.id) + '.pbs')

    # Do not override
    def get_input_file(self, task):
        storage_directory = self.get_or_create_task_storage_directory(task)

        input_path = os.path.join(
            storage_directory,
            'input_' + str(task.id) + '.json')
        ExecutionStrategy._log.info("input_path: %s", input_path)

        return input_path

    # Do not override
    def get_task_storage_directory(self, task):
        task_storage_dir = os.path.join(
            self.get_job_storage_directory(
                self.get_base_storage_directory(), task.job),
            'tasks',
            'task_' + str(task.id))

        ExecutionStrategy._log.info(
            'task storage dir: %s', task_storage_dir)

        return task_storage_dir

    # Do not override
    def get_or_create_task_storage_directory(self, task):
        storage_directory = self.get_task_storage_directory(task)
        ExecutionStrategy._log.info(
            "Storage_directory: %s" % (storage_directory))

        # create directory if needed
        try:
            ExecutionStrategy.make_dirs_chmod(storage_directory, 0o777)
        except Exception as e:
            mess = str(e) + ' - ' + str(traceback.format_exc())
            ExecutionStrategy._log.error(mess)
            task.set_error_message(mess)
            task.set_failed_execution_fields_and_rerun()

        return storage_directory

    # Do not override
    def get_log_file(self, task):
        storage_directory = self.get_or_create_task_storage_directory(task)
        return os.path.join(storage_directory, 'log_' + str(task.id) + '.txt')

    # Do not override
    def get_or_create_storage_directory(self, job):
        storage_directory = \
            self.get_job_storage_directory(
                self.get_base_storage_directory(), job)
        ExecutionStrategy.make_dirs_chmod(storage_directory, 0o777)

        return storage_directory

    def is_execution_strategy(self):
        return True

    # Do not override
    def read_output(self, task):
        output_file = self.get_output_file(task)

        if not os.path.isfile(output_file):
            raise Exception(
                'Expected output file to be created at: ' + \
                str(output_file) + ' but it was not')

        with open(output_file) as json_data:  
            results = json.load(json_data)

        enqueued_object = WorkflowController.get_enqueued_object(task)

        self.on_finishing(enqueued_object, results, task)


from workflow_engine.workflow_controller import WorkflowController
