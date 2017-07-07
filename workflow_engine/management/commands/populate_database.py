from django.core.management.base import BaseCommand
from workflow_engine.models import *
from development.models import Numberr

from django.db import transaction

class Command(BaseCommand):

	@transaction.atomic
	def populate_database(self):
		#create run states
		run_states = ['PENDING', 'QUEUED', 'RUNNING', 'FINISHED_EXECUTION', 'FAILED_EXECUTION', 'FAILED', 'SUCCESS', 'PROCESS_KILLED']

		for run_state_name in run_states:
			run_state = RunState(name=run_state_name)
			run_state.save()

		executable_one = Executable(name='fibonacci', description='get the fibonacci number', executable_path='python3.5 /local1/workflow/workflow_engine/test_executables/fibonacci.py')
		executable_one.save()

		executable_three = Executable(name='adder', description='add numbers together', executable_path='python3.5 /local1/workflow/workflow_engine/test_executables/add.py')
		executable_three.save()

		executable_five = Executable(name='find_primes', description='given a number, find the prime numbers from 0 up to that number', executable_path='python3.5 /local1/workflow/workflow_engine/test_executables/find_primes.py')
		executable_five.save()

tester = Executable(name='test', description='tester', executable_path='teste.foo')
tester.save()

tester2 = JobQueue(name='test', job_strategy_class='test', enqueued_object_class='test', executable=tester)
tester2.save()

		
		# #create job_queues
		job_queue_one = JobQueue(name='fibonacci', job_strategy_class='FibonacciStrategy', enqueued_object_class='Numberr', executable=executable_one)
		job_queue_one.save()

		job_queue_three = JobQueue(name='adder', job_strategy_class='AdderStrategy', enqueued_object_class='Numberr', executable=executable_three)
		job_queue_three.save()

		job_queue_five = JobQueue(name='find_primes', job_strategy_class='FindPrimesStrategy', enqueued_object_class='Numberr', executable=executable_five)
		job_queue_five.save()


		workflow_one = Workflow(name='workflow_one', description='This processes Numberr data')
		workflow_one.save()

		workflow_node_one = WorkflowNode(job_queue=JobQueue.objects.get(name='fibonacci'), is_head=True, workflow=workflow_one)
		workflow_node_one.save()

		workflow_node_two = WorkflowNode(job_queue=JobQueue.objects.get(name='find_primes'), parent=workflow_node_one, workflow=workflow_one)
		workflow_node_two.save()

		workflow_node_three = WorkflowNode(job_queue=JobQueue.objects.get(name='adder'), parent=workflow_node_two, workflow=workflow_one)
		workflow_node_three.save()

		workflow_node_four = WorkflowNode(job_queue=JobQueue.objects.get(name='fibonacci'), parent=workflow_node_two, workflow=workflow_one)
		workflow_node_four.save()

workflow_node_five = WorkflowNode(job_queue=JobQueue.objects.get(name='is_odd_queue'), parent=WorkflowNode.objects.get(id=24), workflow=Workflow.objects.get(id=4))
workflow_node_five.save()


workflow_node_six = WorkflowNode(job_queue=JobQueue.objects.get(name='failure_test_queue'), parent=WorkflowNode.objects.get(id=23), workflow=Workflow.objects.get(id=4))
workflow_node_six.save()



		# #create numbers
number_twenty = Numberr(number=20)
number_twenty.save()

number_one_hundred= Numberr(number=100)
number_one_hundred.save()

number_neg_five = Numberr(number=-5)
number_neg_five.save()

Numberr(value=-5).save()
Numberr(value=20).save()
Numberr(value=35).save()
Numberr(value=50).save()
Numberr(value=1000).save()
Numberr(value=10000).save()


###############

workflow_two = Workflow(name='workflow_two', description='This processes Numberr data')
workflow_two.save()


workflow_node_two = WorkflowNode(job_queue=JobQueue.objects.get(name='find_primes_queue'), is_head=True, workflow=workflow_two)
workflow_node_two.save()

workflow_node_three = WorkflowNode(job_queue=JobQueue.objects.get(name='adder_queue'), parent=workflow_node_two, workflow=workflow_two)
workflow_node_three.save()

workflow_node_five = WorkflowNode(job_queue=JobQueue.objects.get(name='is_odd_queue'), parent=workflow_node_three, workflow=workflow_two)
workflow_node_five.save()

#############


enqueued_object_id = Numberr.objects.get(number=20).id
workflow_node = WorkflowNode.objects.get(id=23)
		
job = Job(enqueued_object_id=enqueued_object_id, workflow_node=workflow_node, run_state=RunState.get_pending_state())
job.save()

enqueued_object_id = Numberr.objects.get(number=100).id
workflow_node = WorkflowNode.objects.get(id=23)
job = Job(enqueued_object_id=enqueued_object_id, workflow_node=workflow_node, run_state=RunState.get_pending_state())
job.save()

enqueued_object_id = Numberr.objects.get(number=-5).id
workflow_node = WorkflowNode.objects.get(id=23)
job = Job(enqueued_object_id=enqueued_object_id, workflow_node=workflow_node, run_state=RunState.get_pending_state())
job.save()

		# from workflow_engine.models import *
		# job = Job.objects.get(id=5)

		# from workflow_engine.models import *
		# job = Job.objects.get(id=2)

	def handle(self, *args, **options):
		self.populate_database()