from workflow_engine.models import *
from execution_runner import run_celery_task
from execution_runner import cancel_task
from workflow_engine.strategies import base_strategy
from development.models import *
from django.conf import settings

import os
import subprocess
import traceback
import sys
import json

class ExecutionStrategy(base_strategy.BaseStrategy):
	#####everthing bellow this can be overriden#####

	#override if needed
	#get the data for the input file
	def get_input(self, enqueued_object, storage_directory, task):
		input_data = {}
		input_data['input'] = str(enqueued_object)

		return input_data

	#override if needed - return the full executable path with all arguments and parameters
	def get_full_executable(self, task):
		try:
			executable = task.job.workflow_node.job_queue.executable
		except Exception as e:
			raise Exception('Could not find executable associated with task: ' + str(task.id) + ' - ' + str(e))

		arguments = executable.static_arguments

		input_file = self.get_input_file(task)

		#populate the input file
		self.create_input_file(input_file, task.get_enqueued_object(), self.get_task_storage_directory(task), task)

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

		return (' '.join(executable_elements))

	#override if needed
	def skip_execution(self, enqueued_object):
		return False

	#####everthing bellow this should not be overriden#####

	#Do not override
	def set_error_message_from_log(self, task):
		try:
			if os.path.isfile(task.log_file):
				result = subprocess.run(['tail', task.log_file], stdout=subprocess.PIPE)
				task.set_error_message(result.stdout.decode("utf-8"))
		except Exception as e:
			print('Something went wrong: ' + str(e))

	#Do not override
	def fail_execution_task(self, task):
		try:
			self.set_error_message_from_log(task)
			self.on_failure(task)
		except Exception as e:
			task.set_error_message(str(e) + ' - ' + str(traceback.format_exc()))

		task.set_failed_execution_state()
		task.set_end_run_time()
		task.job.set_failed_execution_state()
		task.job.set_end_run_time()
		task.rerun()

	#Do not override
	def running_task(self, task):
		try:
			self.on_running(task)
			task.set_start_run_time()
			task.set_running_state()
			job = task.job
			if not job.has_failed_tasks():
				job.set_running_state()
				
		except Exception as e:
			task.set_error_message(str(e) + ' - ' + str(traceback.format_exc()))
			self.fail_task(task)

	#Do not override
	def finish_task(self, task):
		try:
			task.set_finished_execution_state()

			self.read_output(task)

			task.set_success_state()
			task.set_end_run_time()
			if task.job.all_tasks_finished():
				task.job.set_success_state()
				task.job.set_end_run_time()
				task.job.enqueue_next_queue()

		except Exception as e:
			print(str(e) + ' - ' + str(traceback.format_exc()))

			task.set_error_message(str(e) + ' - ' + str(traceback.format_exc()))
			self.fail_task(task)

	#Do not override
	def run_task(self, task):
		try:
			self.prep_task(task)

			task.full_executable = self.get_full_executable(task)
			task.log_file = self.get_log_file(task)
			task.pbs_id = None
			task.save()
			self.run_asynchronous_task(task)
			task.set_queued_state()
		except Exception as e:
			task.set_error_message(str(e) + ' - ' + str(traceback.format_exc()))
			self.fail_task(task)

	#Do not override
	def add_write_to_log_command(self, executable, log_file):
		return str(executable) + ' > ' + str(log_file) + ' 2>&1'

	def kill_pbs_task(self, task):
		if task.pbs_id != None:
			cancel_task.delay(True, task.pbs_id)

	#Do not override
	def run_asynchronous_task(self, task):
		task.clear_error_message()

		if self.skip_execution(task.get_enqueued_object()):
			self.running_task(task)
			self.finish_task(task)
		else:

			if task.pbs_task():
				pbs_file = self.get_pbs_file(task)
				task.create_pbs_file(pbs_file)
				executable = 'qsub ' + pbs_file
				if hasattr(settings, 'CELERY_MESSAGE_QUEUE_NAME'):
					run_celery_task.apply_async(args=[executable, task.id, task.log_file, True], queue = settings.CELERY_MESSAGE_QUEUE_NAME)
				else:
					run_celery_task.delay(executable, task.id, task.log_file, True)
			else:
				executable = self.add_write_to_log_command(task.full_executable, task.log_file)
				if hasattr(settings, 'CELERY_MESSAGE_QUEUE_NAME'):
					run_celery_task.apply_async(args=[executable, task.id, task.log_file, False], queue = settings.CELERY_MESSAGE_QUEUE_NAME)
				else:
					run_celery_task.delay(executable, task.id, task.log_file, False)
				
	#this method creates the input file
	#Do not override
	def create_input_file(self, input_file, enqueued_object, storage_directory, task):
		input_data = self.get_input(enqueued_object, storage_directory, task)

		with open(input_file, 'w') as in_file:
			json.dump(input_data, in_file, indent=2)

	#Do not override
	def get_output_file(self, task):
		storage_directory = self.get_or_create_task_storage_directory(task)
		return os.path.join(storage_directory, 'output_' + str(task.id) + '.json')

	#Do not override
	def get_pbs_file(self, task):
		storage_directory = self.get_or_create_task_storage_directory(task)
		return os.path.join(storage_directory, 'pbs_' + str(task.id) + '.pbs')

	#Do not override
	def get_input_file(self, task):
		storage_directory = self.get_or_create_task_storage_directory(task)
		return os.path.join(storage_directory, 'input_' + str(task.id) + '.json')

	#Do not override
	def get_task_storage_directory(self, task):
		return os.path.join(self.get_job_storage_directory(self.get_base_storage_directory(), task.job), 'tasks','task_' + str(task.id))

	#Do not override
	def get_or_create_task_storage_directory(self, task):
		storage_directory = self.get_task_storage_directory(task)

		#create directory if needed
		if not os.path.exists(storage_directory):
			os.makedirs(storage_directory) 
			subprocess.call(['chmod', '0777', storage_directory]) 

		return storage_directory

	#Do not override
	def get_log_file(self, task):
		storage_directory = self.get_or_create_task_storage_directory(task)
		return os.path.join(storage_directory, 'log_' + str(task.id) + '.txt')

	#Do not override
	def get_or_create_storage_directory(self, job):
		storage_directory = self.get_job_storage_directory(self.get_base_storage_directory(), job)

		#create directory if needed
		if not os.path.exists(storage_directory):
			os.makedirs(storage_directory) 
			subprocess.call(['chmod', '0777', storage_directory]) 

		return storage_directory

	#Do not override
	def is_execution_strategy(self):
		return True

	#Do not override
	def read_output(self, task):
		output_file = self.get_output_file(task)

		if not os.path.isfile(output_file):
			raise Exception('Expected output file to be created at: ' + str(output_file) + ' but it was not')

		result = {}
		with open(output_file) as json_data:  
			results = json.load(json_data)

		self.on_finishing(task.get_enqueued_object(), results, task)