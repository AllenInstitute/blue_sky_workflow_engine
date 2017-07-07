from workflow_engine.strategies import base_strategy
import traceback

class ManualStrategy(base_strategy.BaseStrategy):
	#####everthing bellow this can be overriden#####

	#override if needed
	def task_finished(self, task):
		# enqueued_object = task.get_enqueued_object()
		return True
	
	#####everthing bellow this should not be overriden#####
	#Do not override
	def is_manual_strategy(self):
		return True

	#Do not override
	def check_if_task_finished(self, task):
		finished = False

		if self.task_finished(task):
			finished = True
			task.set_success_state()
			task.set_end_run_time()

			self.on_finishing(task.get_enqueued_object(), {})

			if task.job.all_tasks_finished():
				task.job.set_success_state()
				task.job.set_end_run_time()
				task.job.enqueue_next_queue()

		return finished

	#Do not override
	def run_task(self, task):
		try:
			self.prep_task(task)
			task.set_start_run_time()
			task.set_running_state()
			self.on_running(task)

			job = task.job
			job.set_running_state()

			self.check_if_task_finished(task)

		except Exception as e:
			task.set_error_message(str(e) + ' - ' + str(traceback.format_exc()))
			self.fail_task(task)

			