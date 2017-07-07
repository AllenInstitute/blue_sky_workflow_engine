from django.db import transaction
from workflow_engine.models import *
from development.models import *

@transaction.atomic
def populate_database():
	run_states = ['PENDING', 'QUEUED', 'RUNNING', 'FINISHED_EXECUTION', 'FAILED_EXECUTION', 'FAILED', 'SUCCESS', 'PROCESS_KILLED']

	for run_state_name in run_states:
		run_state = RunState(name=run_state_name)
		run_state.save()

populate_database()