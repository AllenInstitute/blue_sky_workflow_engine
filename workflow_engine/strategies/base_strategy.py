from workflow_engine.models import *
from django.conf import settings

import os

class BaseStrategy(object):
	#####everthing bellow this can be overriden#####

	#override if needed
	#called before the task starts running
	def prep_task(self, task):
		pass

	#override if needed
	#called if the task fails
	def on_failure(self, task):
		pass

	#override if needed
	#called when the task starts running
	def on_running(self, task):
		pass

	#override if needed
	#called after the execution finishes
	#process and save results to the database
	def on_finishing(self, enqueued_object, results):
		pass

	#override if needed
	def get_storage_directory(self, base_storage_directory, job):
		enqueued_object = job.get_enqueued_object()
		return os.path.join(base_storage_directory, str(enqueued_object.id))

	#override if needed
	#this is called when a job is transitioning from a previous queue
	#given the previous job, return an array of enqueued objects for this queue
	def get_objects_for_queue(self, prev_queue_job):
		objects = []
		objects.append(prev_queue_job.get_enqueued_object())
		return objects

	#override if needed
	#return one or more task enqueued objects for a job enqueued object
	def get_task_objects_for_queue(self, enqueued_object):
		objects = []
		objects.append(enqueued_object)

		return objects

	#####everthing bellow this should not be overriden#####
	#Do not override
	def get_base_storage_directory(self):
		return settings.BASE_FILE_PATH

	#Do not override
	def is_execution_strategy(self):
		return False

	#Do not override
	def is_manual_strategy(self):
		return False

	#Do not override
	def get_job_storage_directory(self, base_storage_directory, job):
		return os.path.join(self.get_storage_directory(base_storage_directory, job), 'jobs', 'job_' + str(job.id))

	#Do not override
	def get_or_create_task_storage_directory(self, task):
		storage_directory = self.get_task_storage_directory(task)

		#create directory if needed
		if not os.path.exists(storage_directory):
			os.makedirs(storage_directory)  

		return storage_directory

	#Do not override
	def get_or_create_storage_directory(self, job):
		storage_directory = self.get_job_storage_directory(self.get_base_storage_directory(), job)

		#create directory if needed
		if not os.path.exists(storage_directory):
			os.makedirs(storage_directory)  

		return storage_directory

	#Do not override
	def fail_task(self, task):
		try:
			self.on_failure(task)
		except Exception as e:
			task.set_error_message(str(e) + ' - ' + str(traceback.format_exc()))

		task.set_failed_state()
		task.set_end_run_time()
		task.job.set_failed_state()
		task.job.set_end_run_time()
		task.rerun()
