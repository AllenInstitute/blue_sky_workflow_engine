from django.db import models
from development.strategies import *
import development
import workflow_engine
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import traceback

import os
from django.utils import timezone
from celery.task.control import revoke
from django.conf import settings
import sys
import re

ZERO = 0
ONE = 1
SECONDS_IN_MIN = 60
TWO = 2

class Executable(models.Model):
	name = models.CharField(max_length=255, unique=True)
	description = models.CharField(max_length=255, null=True)
	static_arguments = models.CharField(max_length=255, null=True)
	executable_path = models.CharField(max_length=1000)
	pbs_executable_path = models.CharField(max_length=1000, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	pbs_processor = models.CharField(max_length=255, default='vmem=6g')
	pbs_walltime = models.CharField(max_length=255, default='walltime=5:00:00')
	pbs_queue = models.CharField(max_length=255, default='lims')

	def get_created_at(self):
		return timezone.localtime(self.created_at).strftime('%m/%d/%Y %I:%M:%S')

	def get_updated_at(self):
		return timezone.localtime(self.updated_at).strftime('%m/%d/%Y %I:%M:%S')

	def get_job_queues(self):
		try:
			results = JobQueue.objects.filter(executable=self)
		except Exception as e:
			result = []

		return results

# Create your models here.
class JobQueue(models.Model):
	name = models.CharField(max_length=255, unique=True)
	description = models.CharField(max_length=255, null=True)
	job_strategy_class = models.CharField(max_length=255)
	enqueued_object_class = models.CharField(max_length=255)
	executable = models.ForeignKey(Executable, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def get_strategy(self):
		return eval(self.job_strategy_class)()

	def get_created_at(self):
		return timezone.localtime(self.created_at).strftime('%m/%d/%Y %I:%M:%S')

	def get_updated_at(self):
		return timezone.localtime(self.updated_at).strftime('%m/%d/%Y %I:%M:%S')

	def get_workflow_nodes(self):
		try:
			results = WorkflowNode.objects.filter(job_queue=self)
		except Exception as e:
			result = []

		return results

class RunState(models.Model):
	name = models.CharField(max_length=255, unique=True)

	def __str__(self):
		return self.name

	@staticmethod
	def is_failed_type_state(job_state_name):
		return (job_state_name == RunState.get_failed_execution_state().name or job_state_name == RunState.get_failed_state().name or job_state_name == RunState.get_process_killed_state().name)

	def is_running_type_state(job_state_name):
		return (job_state_name == RunState.get_pending_state().name or job_state_name == RunState.get_running_state().name or job_state_name == RunState.get_queued_state().name or job_state_name == RunState.get_finished_execution_state().name)

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

class Workflow(models.Model):
	name = models.CharField(max_length=255)
	description = models.CharField(max_length=255, null=True)
	disabled = models.BooleanField(default=False)
	use_pbs = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def get_head_workfow_nodes(self):
		return WorkflowNode.objects.filter(is_head=True, workflow=self.id)

	@staticmethod
	def start_workflow(worklfow_name, enqueued_object):
		workflow = Workflow.objects.get(name=worklfow_name)
		workflow_nodes = WorkflowNode.objects.filter(workflow=workflow, parent=None)

		if len(workflow_nodes) != ONE:
			raise Exception('Expected to find a single head workflow node but found: ' + str(len(workflow_nodes)))

		workflow_node = workflow_nodes[ZERO]

		job = Job()
		job.enqueued_object_id=enqueued_object.id
		job.workflow_node=workflow_node
		job.run_state=RunState.get_pending_state()
		job.priority = workflow_node.priority
		job.save()
		job.run_jobs()


class WellKnownFile(models.Model):
	attachable_id = models.PositiveIntegerField()
	attachable_type = models.ForeignKey(ContentType)
	well_known_file_type = models.CharField(max_length=255)
	content_object = GenericForeignKey('attachable_type', 'attachable_id')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	@staticmethod
	def set(full_path, attachable_object, well_known_file_type, task=None):
		#make sure file is valid
		WellKnownFile.verify_file_exists(full_path)

		well_known_file = WellKnownFile.get_or_create_well_known_file(attachable_object, well_known_file_type)
		well_known_file.create_file_record_if_needed(full_path, task)

	#staticmethod
	def get(attachable_object, well_known_file_type):
		result = None

		try:
			well_known_file = WellKnownFile.objects.get(attachable_id=attachable_object.id, well_known_file_type=well_known_file_type)
			file_record = well_known_file.get_most_recent_file_record()
			result = file_record.get_full_name()
		except:
			result = None
	
		return result

	def get_next_order(self):
		order = ZERO

		for file_record in self.get_file_records():
			if file_record.order >= order:
				order = file_record.order + ONE

		return order

	@staticmethod
	def verify_file_exists(full_path):
		if not os.path.exists(full_path):
			raise Exception('Expected file to exist at: ' + str(full_path) + ' but it does not')

	@staticmethod
	def get_or_create_well_known_file(attachable_object, well_known_file_type):
		try:
			well_known_file = WellKnownFile.objects.get(attachable_id=attachable_object.id, well_known_file_type=well_known_file_type)
		except:
			well_known_file = WellKnownFile(content_object=attachable_object, well_known_file_type=well_known_file_type)
			well_known_file.save()

		return well_known_file

	def create_file_record_if_needed(self, full_path, task):
		filename = os.path.basename(full_path)
		storage_directory = os.path.dirname(full_path)

		most_recent_file = self.get_most_recent_file_record()

		if not most_recent_file or most_recent_file.filename != filename or most_recent_file.storage_directory != storage_directory:
			file_record = FileRecord(filename=filename, storage_directory=storage_directory, order=self.get_next_order(), well_known_file=self, task=task)
			file_record.save()
		else:
			most_recent_file.task = task
			most_recent_file.save()

	def get_file_records(self):
		return FileRecord.objects.filter(well_known_file_id=self.id).order_by('order')

	def get_most_recent_file_record(self):
		try:
			file_records = self.get_file_records()
			last_element = len(file_records) - ONE
			result = file_records[last_element]
		except:
			result = None

		return result

class WorkflowNode(models.Model):
	job_queue = models.ForeignKey(JobQueue)
	parent = models.ForeignKey('self', null=True)
	is_head = models.BooleanField(default=False)
	workflow = models.ForeignKey(Workflow)
	disabled = models.BooleanField(default=False)
	batch_size = models.IntegerField(default=50)
	priority = models.IntegerField(default=50)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	overwrite_previous_job = models.BooleanField(default=True)
	max_retries = models.IntegerField(default=3)

	def get_node_name(self):
		return self.job_queue.name + '(' + str(self.get_total_number_of_jobs()) + ') ' + str(self.get_number_of_queued_and_running_jobs()) + ' / '+ str(self.batch_size)

	def get_workflow_name(self):
		return self.workflow.name

	def get_strategy(self):
		return self.job_queue.get_strategy()

	def get_children(self):
		return WorkflowNode.objects.filter(parent=self)

	def get_total_number_of_jobs(self):
		return Job.objects.filter(workflow_node=self, archived=False).count()

	def get_number_of_queued_and_running_jobs(self):
		return len(self.get_queued_and_running_jobs())

	def get_queued_and_running_jobs(self):
		try: 
			result = Job.objects.filter(run_state_id__in=[RunState.get_queued_state().id, RunState.get_running_state().id], workflow_node=self, archived=False)
		except Exception as e:
			result = []

		return result

	def run_workflow_node_jobs(self):
		try:
			if not self.workflow.disabled and not self.disabled:
				#check if more jobs can be run
				batch_size = self.batch_size

				try:
					number_of_queued_and_running_jobs = self.get_number_of_queued_and_running_jobs()
				except Exception as e:
					number_of_queued_and_running_jobs = ZERO

				number_jobs_to_run = batch_size - number_of_queued_and_running_jobs

				#run more jobs
				if number_jobs_to_run > ZERO:

					try:
						pending_jobs = Job.objects.filter(run_state_id=RunState.get_pending_state().id, workflow_node=self, archived=False).order_by('priority', '-updated_at')
					except Exception as e:
						pending_jobs = []

					for i in range(number_jobs_to_run):
						if i < len(pending_jobs):

							job = pending_jobs[i]
							job.run()

		except Exception as e:
			print('Semothing went wrong running jobs:  ' + str(e))

class Job(models.Model):
	enqueued_object_id = models.IntegerField()
	workflow_node = models.ForeignKey(WorkflowNode)
	run_state = models.ForeignKey(RunState)
	duration = models.DurationField(null=True)
	start_run_time = models.DateTimeField(null=True)
	end_run_time = models.DateTimeField(null=True)
	error_message = models.TextField(null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	priority = models.IntegerField(default=50)
	archived = models.NullBooleanField(default=False)

	def archive_record(self):
		for task in self.get_tasks():
			task.archive_record()

		self.archived = True
		self.save()

	def get_created_at(self):
		return timezone.localtime(self.created_at).strftime('%m/%d/%Y %I:%M:%S')

	def get_updated_at(self):
		return timezone.localtime(self.updated_at).strftime('%m/%d/%Y %I:%M:%S')

	def get_color_class(self):
		color = 'color_' + self.run_state.name.lower()

		return color

	def set_queued_state(self):
		self.run_state = RunState.get_queued_state()
		self.save()

	def get_enqueued_object_display(self):
		result = None
		try:
			enqueued_object = self.get_enqueued_object()
			result = str(enqueued_object)
		except:
			result = None

		return result

	def get_enqueued_object_class_type(self):
		return self.workflow_node.job_queue.enqueued_object_class

	def set_error_message(self, error_message, task):

		if not task:
			self.error_message = 'job failed: ' + error_message
		elif error_message != None:
			self.error_message = 'task with id of ' + str(task.id) + ' failed: '  + error_message
		else:
			self.error_message = 'task with id of ' + str(task.id) + ' failed'

		self.save()

	def clear_error_message(self):
		self.error_message = None
		self.save()

	def can_rerun(self):
		run_state_name = self.run_state.name
		return (run_state_name == 'PENDING' or run_state_name == 'FAILED' or run_state_name == 'SUCCESS' or run_state_name == 'PROCESS_KILLED' or run_state_name == 'FAILED_EXECUTION')

	def set_pending_state(self):
		self.run_state = RunState.get_pending_state()
		self.save()

	def set_failed_state(self):
		self.run_state = RunState.get_failed_state()
		self.save()
		self.run_jobs()

	def set_failed_execution_state(self):
		self.run_state = RunState.get_failed_execution_state()
		self.save()
		self.run_jobs()

	def set_running_state_from_queued(self):
		if(self.run_state.name == 'QUEUED'):
			self.set_running_state()

	def set_running_state(self):
		self.run_state = RunState.get_running_state()
		self.save()

	def set_success_state(self):
		self.run_state = RunState.get_success_state()
		self.save()
		self.run_jobs()

	def set_process_killed_state(self):
		self.run_state = RunState.get_process_killed_state()
		self.save()
		self.run_jobs()

	def get_enqueued_object(self):
		enqueued_object_class = eval(self.workflow_node.job_queue.enqueued_object_class)
		return enqueued_object_class.objects.get(id=self.enqueued_object_id)

	def get_strategy(self):
		return self.workflow_node.get_strategy()

	def archive_record(self):
		self.archived = True
		self.save()

	def remove_tasks(self, resused_tasks):
		strategy = self.get_strategy()
		for task in self.get_tasks():
			if task.id not in resused_tasks:
				task.archived = False
				task.save()

	def create_tasks(self):
		resused_tasks = {}
		strategy = self.get_strategy()
		pending_state = RunState.get_pending_state()

		task_objects = strategy.get_task_objects_for_queue(self.get_enqueued_object())

		for task_object in task_objects:
			if self.workflow_node.overwrite_previous_job:
				try:
					#try to reuse a previous task
					task = Task.objects.get(enqueued_task_object_id=task_object.id, enqueued_task_object_class=type(task_object).__name__,job=self)
					task.run_state = pending_state
					task.archived = False
					task.retry_count = ZERO
					task.save()
				except:
					task = Task(enqueued_task_object_id=task_object.id, enqueued_task_object_class=type(task_object).__name__, run_state=pending_state, job=self)
					task.save()
			else:
				task = Task(enqueued_task_object_id=task_object.id, enqueued_task_object_class=type(task_object).__name__, run_state=pending_state, job=self)
				task.save()

			resused_tasks[task.id] = True

		return resused_tasks

	def get_tasks(self):
		return Task.objects.filter(job_id=self.id, archived=False)

	def number_of_tasks(self):
		return len(self.get_tasks())

	def set_for_run_if_valid(self):
		if self.can_rerun():
			self.set_for_run()

	def set_for_run(self):
		self.set_pending_state()
		self.run_jobs()

	def prep_job(self):
		strategy = self.get_strategy()
		strategy.prep_job(self)

	def run(self):
		try:
			self.set_queued_state()

			self.set_start_run_time()
			self.clear_error_message()

			self.prep_job()

			resused_tasks = self.create_tasks()

			self.remove_tasks(resused_tasks)

			for task in self.get_tasks():
				task.run_task()

		except Exception as e:
			self.set_error_message(str(e) + ' - ' + str(traceback.format_exc()), None)
			self.set_failed_state()

	def run_jobs(self):
		self.workflow_node.run_workflow_node_jobs()

	def get_start_run_time(self):
		result = None
		if self.start_run_time != None:
			result = timezone.localtime(self.start_run_time).strftime('%m/%d/%Y %I:%M:%S')

		return result

	def get_end_run_time(self):
		result = None
		if self.end_run_time != None:
			result = timezone.localtime(self.end_run_time).strftime('%m/%d/%Y %I:%M:%S')

		return result

	def get_duration(self):
		result = None
		if self.duration != None:
			total_seconds = self.duration.seconds
			minutes = total_seconds / SECONDS_IN_MIN

			result = str(round(minutes,TWO)) + ' min'

		return result

	def set_start_run_time(self):
		self.start_run_time = timezone.now()
		self.end_run_time = None
		self.duration = None
		self.save()

	def set_end_run_time(self):
		self.end_run_time = timezone.now()
		self.duration = str(self.end_run_time - self.start_run_time)
		self.save()

	def enqueue_next_queue(self):
		children = self.workflow_node.get_children()
		for child in children:
			strategy = child.get_strategy()
			enqueued_objects = strategy.get_objects_for_queue(self)
			for enqueued_object in enqueued_objects:

				#try to get the job
				jobs = Job.objects.filter(enqueued_object_id=enqueued_object.id, workflow_node_id=child.id, archived=False)

				if len(jobs) > ZERO:
					index = ZERO
					for job in jobs:
						#reset job if needed
						if index == ZERO:
							job.run_state = RunState.get_pending_state()
							job.priority = child.priority
							job.archived = False
							job.save()
							job.set_for_run()
							
						#should not have more than one job but just in case
						else:
							job.archived = True
							job.save()

						index+=ONE
				else:
					#create the job if needed
					job = Job(enqueued_object_id=enqueued_object.id, workflow_node=child, run_state=RunState.get_pending_state(),priority=child.priority)
					job.save()
					job.set_for_run()


	#check if all tasks have finished
	def all_tasks_finished(self):
		all_finished = True

		for task in self.get_tasks():
			if all_finished:
				all_finished = task.in_success_state()

		return all_finished

	def kill_tasks(self):
		for task in self.get_tasks():
			task.kill_task()

class Datafix(models.Model):
	name = models.CharField(max_length=255)
	timestamp = models.CharField(max_length=255)
	run_at = models.DateTimeField(null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	@staticmethod
	def get_extension(filename):
		try:
			extension = os.path.splitext(filename)[ONE]
		except:
			extension = ''

		return extension

	def get_workflow_path():
		return os.path.dirname(workflow_engine.__file__)

	def get_development_path():
		return os.path.dirname(development.__file__)

	@staticmethod
	def get_development_strategy_path():
		return os.path.join(Datafix.get_development_path(),'strategies/')

	@staticmethod
	def get_workflow_datafix_path():
		return os.path.join(Datafix.get_workflow_path(),'datafixes/')

	@staticmethod
	def get_development_datafix_path():
		return os.path.join(Datafix.get_development_path(),'datafixes/')

	@staticmethod
	def create_datafix_records_if_needed():
		workflow_datafix_dir = Datafix.get_workflow_datafix_path()
		dev_datafix_dir = Datafix.get_development_datafix_path()

		files = os.listdir(workflow_datafix_dir) + os.listdir(dev_datafix_dir)

		for file in files:
			if Datafix.get_extension(file) == '.py' and os.path.basename(file) != '__init__.py':
				name = os.path.basename(file).replace('.py', '')

				try:
					Datafix.objects.get(name=name)
				except ObjectDoesNotExist:
					Datafix.create_datafix(name)

	@staticmethod
	def create_datafix(name):
		workflow_datafix_dir = Datafix.get_workflow_datafix_path()
		datafix_dir = Datafix.get_development_datafix_path()

		file_name = datafix_dir + name + '.py'
		workflow_file_name = workflow_datafix_dir + name + '.py'

		if not os.path.exists(file_name) and not os.path.exists(workflow_file_name):
			raise Exception('Expected datafix file to exist at either: ' + file_name + ' or ' + workflow_file_name)

		timestamp = re.sub(r"(.*_)", "", name)

		datafix = Datafix(name=name, timestamp=timestamp)
		datafix.save()

		return datafix

	def run(self):
		print('running datafix: ' + self.name)

		workflow_datafix_dir =  Datafix.get_workflow_datafix_path()
		datafix_dir = Datafix.get_development_datafix_path()

		file_name = datafix_dir + self.name + '.py'
		workflow_file_name = workflow_datafix_dir + self.name + '.py'

		if os.path.exists(file_name):
			self.run_datafix(file_name)
		elif os.path.exists(workflow_file_name):
			self.run_datafix(workflow_file_name)
		else:
			raise Exception('Expected datafix file to exist at either: ' + file_name + ' or ' + workflow_file_name)

		self.run_at = timezone.now()
		self.save()

	def run_datafix(self, datafix_file):
		with open(datafix_file,"r") as code:
			exec(code.read())

	def create_file(self, use_workflow_engine):

		if use_workflow_engine:
			datafix_dir = Datafix.get_workflow_datafix_path()
		else:
			datafix_dir = Datafix.get_development_datafix_path()

		if not os.path.exists(datafix_dir):
			os.makedirs(datafix_dir)

		file_name = datafix_dir + self.name + '.py'

		with open(file_name, 'w') as datafix_file:
			datafix_file.write('#!/usr/bin/python\n')
			datafix_file.write('from django.db import transaction\n')
			datafix_file.write('from workflow_engine.models import *\n')
			datafix_file.write('from development.models import *\n\n')
			datafix_file.write('@transaction.atomic\n')
			datafix_file.write('def populate_database():\n')
			datafix_file.write('    #put your code here\n')
			datafix_file.write("    print('populating database...')\n")
			datafix_file.write('\n')
			datafix_file.write('populate_database()')
		
class Task(models.Model):

	enqueued_task_object_id = models.IntegerField(null=True)
	enqueued_task_object_class = models.CharField(max_length=255, null=True)
	job = models.ForeignKey(Job)
	archived = models.NullBooleanField(default=False)
	run_state = models.ForeignKey(RunState)
	full_executable = models.CharField(max_length=1000, null=True)
	error_message = models.TextField(null=True)
	log_file = models.CharField(max_length=255, null=True)
	input_file = models.CharField(max_length=255, null=True)
	output_file = models.CharField(max_length=255, null=True)
	pbs_file = models.CharField(max_length=255, null=True)
	start_run_time = models.DateTimeField(null=True)
	end_run_time = models.DateTimeField(null=True)
	duration = models.DurationField(null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	pbs_id = models.CharField(max_length=255, null=True)
	retry_count = models.IntegerField(default=0)

	def __str__(self):
		return 'task: ' + str(self.id)

	def get_created_at(self):
		return timezone.localtime(self.created_at).strftime('%m/%d/%Y %I:%M:%S')

	def get_updated_at(self):
		return timezone.localtime(self.updated_at).strftime('%m/%d/%Y %I:%M:%S')

	def set_error_message(self, error_message):

		self.error_message = str(error_message)
		self.save()
		self.job.set_error_message(self.error_message, self)

	def pbs_task(self):
		return self.job.workflow_node.workflow.use_pbs

	def kill_task(self):
		self.set_process_killed_state()
		revoke(self.id, terminate=True)
		strategy = self.get_strategy()
		if strategy.is_execution_strategy():
			strategy.kill_pbs_task(self)

		self.set_end_run_time()

	def get_start_run_time(self):
		result = None
		if self.start_run_time != None:
			result = timezone.localtime(self.start_run_time).strftime('%m/%d/%Y %I:%M:%S')

		return result

	def get_end_run_time(self):
		result = None
		if self.end_run_time != None:
			result = timezone.localtime(self.end_run_time).strftime('%m/%d/%Y %I:%M:%S')

		return result

	def get_enqueued_object_display(self):
		result = None
		try:
			enqueued_object = self.get_enqueued_object()
			result = str(enqueued_object)
		except:
			result = None

		return result

	def get_duration(self):
		result = None
		if self.duration != None:
			total_seconds = self.duration.seconds
			minutes = total_seconds / SECONDS_IN_MIN

			result = str(round(minutes,TWO)) + ' min'

		return result

	def set_start_run_time(self):
		self.start_run_time = timezone.now()
		self.end_run_time = None
		self.duration = None
		self.save()

	def set_end_run_time(self):
		self.end_run_time = timezone.now()
		self.duration = str(self.end_run_time - self.start_run_time)
		self.save()

	def can_rerun(self):
		run_state_name = self.run_state.name
		return (run_state_name == 'PENDING' or run_state_name == 'FAILED' or run_state_name == 'SUCCESS' or run_state_name == 'PROCESS_KILLED' or run_state_name == 'FAILED_EXECUTION')

	def get_color_class(self):
		color = 'color_' + self.run_state.name.lower()

		return color

	def clear_error_message(self):
		self.error_message = None
		self.save()

	def get_strategy(self):
		return self.job.get_strategy()

	def fail_task(self):
		strategy = self.get_strategy()
		strategy.fail_task(self)

	def finish_task(self):
		strategy = self.get_strategy()
		strategy.finish_task(self)

	def get_max_retries(self):
		return self.job.workflow_node.max_retries

	def rerun(self):
		if self.can_rerun and self.retry_count < self.get_max_retries():
			self.run_task()

	def increment_retry_count(self):
		self.retry_count = self.retry_count + ONE
		self.save()

	def reset_retry_count(self):
		self.retry_count = ZERO
		self.save()

	def run_task(self):
		self.increment_retry_count()
		self.set_start_run_time()
		strategy = self.get_strategy()
		strategy.run_task(self)

	def set_pending_state(self):
		self.run_state = RunState.get_pending_state()
		self.save()

	def set_process_killed_state(self):
		self.run_state = RunState.get_process_killed_state()
		self.save()

	def set_running_state(self):
		self.run_state = RunState.get_running_state()
		self.save()

	def set_finished_execution_state(self):
		self.run_state = RunState.get_finished_execution_state()
		self.save()

	def set_failed_state(self):
		self.run_state = RunState.get_failed_state()
		self.save()

	def set_failed_execution_state(self):
		self.run_state = RunState.get_failed_execution_state()
		self.save()

	def set_success_state(self):
		self.run_state = RunState.get_success_state()
		self.save()

	def set_queued_state(self):
		self.run_state = RunState.get_queued_state()
		self.save()

	def in_success_state(self):
		return (self.run_state.name == RunState.get_success_state().name)

	def get_enqueued_job_object(self):
		return self.job.get_enqueued_object()

	def get_job_queue(self):
		return self.job.workflow_node.job_queue

	def get_executable(self):
		return self.get_job_queue().executable

	def get_task_name(self):
		return ('task_' + str(self.id))

	def get_umask(self):
		return '022'

	def get_pbs_commands(self):
		executable = self.get_executable()

		commands = []
		commands.append('#!/bin/bash')
		commands.append('#PBS -q ' + executable.pbs_queue)
		commands.append('#PBS -l ' + executable.pbs_processor)
		commands.append('#PBS -l ' + executable.pbs_walltime)
		commands.append('#PBS -N ' + self.get_task_name())
		commands.append('#PBS -V') # Import system variables
		commands.append('#PBS -r n') # Not re-runable
		commands.append('#PBS -W umask=' + self.get_umask()) # file creation permissions
		commands.append('#PBS -j oe') # Join error and output streams
		commands.append('#PBS -o ' + self.log_file)
		commands.append('umask ' + self.get_umask()) # Shell command to open umask
		commands.append(self.full_executable)
		commands.append('rtn_code=$?')
		commands.append('/shared/utils.x86_64/python-2.7/bin/python ' + settings.PBS_FINISH_PATH + ' $rtn_code ' + str(self.id))

		return commands

	def create_pbs_file(self, pbs_file):
		commands = self.get_pbs_commands()

		file_handle = open(pbs_file, 'w')
		for command in commands:
			file_handle.write(command + '\n')

		file_handle.close()

		self.pbs_file = pbs_file
		self.save()

	def get_enqueued_object(self):
		if self.enqueued_task_object_class == None:
			raise Exception('enqueued_task_object_class is nil for task: ' + str(self.id))

		if self.enqueued_task_object_id == None:
			raise Exception('enqueued_task_object_id is nil for task: ' + str(self.id))

		enqueued_object_class = eval(self.enqueued_task_object_class)
		enqueued_object = enqueued_object_class.objects.get(id=self.enqueued_task_object_id)

		if enqueued_object == None:
			raise Exception('enqueued_object does not exist for enqueued_object_class of ' + str(self.enqueued_task_object_class) + ' and id of ' + str(self.enqueued_task_object_id))  

		return enqueued_object

	def get_file_records(self):
		results = []
		file_records = FileRecord.objects.filter(task=self)
		for file_record in file_records:
			results.append(file_record.get_full_name())

		return results

class FileRecord(models.Model):
	filename = models.CharField(max_length=255)
	storage_directory = models.CharField(max_length=500)
	order = models.IntegerField(default=0)
	well_known_file = models.ForeignKey(WellKnownFile)
	task = models.ForeignKey(Task, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def get_full_name(self):
		return os.path.join(self.storage_directory, self.filename)