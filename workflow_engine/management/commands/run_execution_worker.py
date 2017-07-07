import pika
from workflow_engine.models import RunState, Task
from django.conf import settings

STATE = 0
TASK_ID = 1
PBS_ID = 2

connection = pika.BlockingConnection(pika.ConnectionParameters(host=settings.MESSAGE_QUEUE_HOST))
channel = connection.channel()

channel.queue_declare(queue='tasks')

def process_running(task, strategy):
	strategy.running_task(task)

def process_finished_execution(task, strategy):
	strategy.finish_task(task)

def process_failed_execution(task, strategy):
	strategy.fail_execution_task(task)

def callback(ch, method, properties, body):
	body = body.decode("utf-8") 
	print(" [x] Received " + str(body))

	try:
		body_data = body.split(',')
		state = body_data[STATE]
		task_id = body_data[TASK_ID]

		task = Task.objects.get(id=task_id)

		strategy = task.get_strategy()
		if state == RunState.get_running_state().name:
			process_running(task, strategy)
		elif state == RunState.get_finished_execution_state().name:
			process_finished_execution(task, strategy)
		elif state == RunState.get_failed_execution_state().name:
			process_failed_execution(task, strategy)
		elif state == 'PBS_ID':
			task.pbs_id = str(body_data[PBS_ID])
			task.save()

	except Exception as e:
		print('Something went wrong: ' + str(e))

channel.basic_consume(callback,queue='tasks',no_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()