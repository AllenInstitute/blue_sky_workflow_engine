class BlueSkyStateMachine:

	def __init__(self):
		self.transitions = {} 

	def add_transition(self, state, transitions):
		self.transitions[state] = transitions

	def transition(self, model, state_machine_field, to_state):
		try:
			#make sure field exists
			model._meta.get_field(state_machine_field)
			current_state = getattr(model, state_machine_field)

			if current_state in self.transitions:
				transitions = self.transitions[current_state]
				if to_state in transitions:
					setattr(model, state_machine_field, to_state)
					model.save()
				else:
					raise Exception('State: ' + str(current_state) + ' cannot transition to ' + str(to_state))

			else:
				raise Exception('State: ' + str(current_state) + ' does not have any transitions')

		except FieldDoesNotExist:
			raise Exception('Field named: ' + str(state_machine_field) + ' does not exist')
