import yaml

class StateMachine:
    def __init__(self, n, s, ts):
        self.name = n
        self.states = s
        self.num_states = len(s)
        self.transitions = [list(t) for t in ts]
        self.pairs = self.transition_pairs_from_table()

    @classmethod
    def from_yaml(cls, y):
        definition = yaml.load(y)
        machines = []

        for k,v in definition.items():
            machines.append(cls(k,
                                v['states'],
                                v['transitions']))

        return machines

    @classmethod
    def from_yaml_file(cls, path):
        with open(path, 'r') as f:
            return cls.from_yaml(f)

    def transition_pairs_from_table(self):
        pairs = []

        for source in range(self.num_states):
            for target in range(self.num_states):
                if self.transitions[source][target] == 'o':
                    pairs.append((source, target))

        return pairs


if "__main__" == __name__:
    l = StateMachine.from_yaml_file('/local1/git/blue_sky_workflow_engine/workflow_engine/test/states.yml')

    for i in l:
        print(i.name)
        print(i.states)
        print(i.transitions)
        print(i.pairs)

