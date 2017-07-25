from workflow_engine.file_holder import FileHolder

class LogHolder(object):
	def add_file_holder(self, file_holder):
		self.file_holders.append(file_holder)

	def __init__(self):
		self.task_id = None
		self.file_holders = []
		self.full_executable = None
		self.job_queue_name = None
		self.job_queue_id = None
		self.executable_id = None
		self.executable_name = None
		self.run_state = None
		self.enqueued_object_id = None
		self.error_message = None