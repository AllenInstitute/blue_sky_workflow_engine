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
from celery import chain
from celery.exceptions import SoftTimeLimitExceeded
from workflow_engine.celery.signatures import (
    enqueue_next_queue_signature,
    kill_moab_task_signature,
    process_pbs_id_signature,
    process_running_signature,
    submit_moab_task_signature,
    failed_execution_handler_signature,
)
#from workflow_engine.celery.error_handler import failed_execution_handler
#from workflow_engine.celery.moab_tasks import submit_moab_task
#from workflow_engine.celery.local_tasks import submit_worker_task
from workflow_client.tasks.circus_signatures import (
    submit_task_signature,
    kill_task_signature
)


class ExecutionStrategy(base_strategy.BaseStrategy):
    _log = logging.getLogger('workflow_engine.strategies.execution_strategy')
    # ## ## everthing below this can be overriden# ## ##

    # override if needed
    # get the data for the input file
    def get_input(self, enqueued_object, storage_directory, task):
        '''Override to populate and write input.

        Parameters
        ----------
        enqueued_object : Enqueueable
            primary database object to be manipulated
        storage_directory : string
            where to store input files
        task : Task
            to be run

        Returns
        -------
        dict
            strategy-specific input
        '''
        input_data = {}
        input_data['input'] = str(enqueued_object)

        return input_data

    def get_remote_queue(self, task):
        '''helper method to get the remote blue_sky worker queue name

        Parameters
        ----------
        task : Task
            used to access the executable

        Returns
        -------
        string
            well-known string used to choose which worker to submit task to
        '''
        return task.get_executable().remote_queue

    def get_task_arguments(self, task, write_files=False):
        '''Override to generate command-line arguments at run time.

        Parameters
        ----------
        task : Task
            to be run
        write_files : boolean
            generate files as a side effect

        Returns
        -------
        list or None
            argument strings
        '''
        return None

    # override if needed
    def get_full_executable(self, task):
        '''return the command with all arguments and parameters
        '''
        try:
            executable = task.get_executable()
            ExecutionStrategy._log.info(
                'executable %s' % (str(executable)))
        except Exception as e:
            raise Exception(
                'Could not find executable associated with task: ' + \
                str(task.id) + ' - ' + str(e))

        arguments = executable.static_arguments
        ExecutionStrategy._log.info('static arguments %s' % (str(arguments)))

        task_arguments = self.get_task_arguments(task)

        input_file = self.get_input_file(task)
        ExecutionStrategy._log.info('input file %s' % (str(input_file)))

        # populate the input file
        storage_dir = self.get_task_storage_directory(task)

        enqueued_object = task.enqueued_task_object
        
        ExecutionStrategy._log.info(
            'enqueued_object: %s',
            str(enqueued_object))

        if input_file is not None:
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

        if arguments is not None:
            executable_elements.append(arguments)

        if task_arguments is not None:
            executable_elements.extend(task_arguments)

        if input_file is not None:
            executable_elements.append('--input_json')
            executable_elements.append(input_file)

        if output_file is not None:
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

    # ## ## everthing below this should not be overriden# ## ##

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
        if task.pbs_task():
            if task.pbs_id is not None:
                kill_moab_task_signature.delay(task.id)
        else:
            if self.get_remote_queue(task) == 'circus':
                if task.pbs_id is not None:
                    kill_task_signature.delay(int(task.pbs_id))

    # Do not override
    def run_asynchronous_task(self, task):
        task.clear_error_message()

        if self.skip_execution(task.enqueued_task_object):
            # TODO: make this a "skip" remote queue
            ExecutionStrategy._log.info('skipping execution')
            self.running_task(task)
            self.finish_task(task)
        else:
            queue_name = self.get_remote_queue(task)
            if queue_name in ['pbs', 'spark_moab']:
                queue_name = settings.MOAB_MESSAGE_QUEUE_NAME
            elif queue_name == 'local':
                queue_name = settings.LOCAL_MESSAGE_QUEUE_NAME
            elif queue_name == 'circus':
                queue_name = 'circus'
            else:
                ExecutionStrategy._log.warn('Unknown queue: {}'.format(queue_name))

            if task.pbs_task():
                submit_moab_task_signature.delay(task.id)
            else:
                if queue_name == 'circus':
                    executable = task.get_executable()

                    env = {
                        k_v[0]: k_v[1] for k_v in (
                            pair.split('=', 1)
                            for pair in executable.environment_vars()
                        )
                    }

                    env.update({
                        'BLUE_SKY_JOB_QUEUE':
                            task.job.workflow_node.job_queue.name.replace(
                                ' ', '\\ '
                            )
                    })

                    try:
                        chain(
                            submit_task_signature.clone((
                                "task_{}".format(task.id),
                                self.get_pbs_file(task),
                                executable.executable_path,
                                self.get_input_file(task),
                                self.get_output_file(task),
                                executable.static_arguments,
                                self.get_or_create_task_storage_directory(task),
                                env),
                            ).set(
                                time_limit=11
                            ),
                            process_pbs_id_signature.clone(
                                (task.id, True)
                            ).set(
                                time_limit=11
                            ),
                            process_running_signature.clone(
                                (task.id,)
                            ).set(
                                time_limit=11,
                                immutable=True
                            )
                        ).apply_async(
                            time_limit=11,
                            link_error=failed_execution_handler_signature.clone(
                                (task.id,)
                            )
                        )
                    except SoftTimeLimitExceeded:
                        ExecutionStrategy._log.warning('Submit Task Timeout')

    def get_dynamic_arguments(self, task):
        return []

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
        os.chmod(input_file, 0o664)

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
    # TODO: the data flow in constructing this path is overly complex
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

        if output_file is None:
            results = {}
        else:
            if not os.path.isfile(output_file):
                raise Exception(
                    'Expected output file to be created at: ' + \
                    str(output_file) + ' but it was not')
    
            with open(output_file) as json_data:
                results = json.load(json_data)

        self.on_finishing(task.enqueued_task_object, results, task)
