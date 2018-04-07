from workflow_client.client_settings import settings_attr_dict
import yaml
import logging

class StateMachineYaml:
    _log = logging.getLogger('workflow_engine.state_machine_yaml')

    @classmethod
    def from_yaml(cls, y):
        description = yaml.load(y)

        # TODO: clean this up - enum?
        machines = { 
            k: {
                'states': settings_attr_dict(
                    { k: k for k in v['states']}),
                'transitions':
                    StateMachineYaml.transition_pairs_from_table(
                        v['states'],
                        v['transitions'] )}
            for k,v in description.items() }

        return machines

    @classmethod
    def from_yaml_file(cls, path):
        with open(path, 'r') as f:
            return cls.from_yaml(f)

    @classmethod
    def transition_pairs_from_table(cls, states, table):
        num_states = len(states)
        transitions = { s: set() for s in states }

        for source in range(num_states):
            for target in range(num_states):
                if table[source][target] == 'o':
                    transitions[states[source]].add(
                        states[target])

        return transitions
