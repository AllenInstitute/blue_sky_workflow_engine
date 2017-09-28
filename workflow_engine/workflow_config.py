import yaml

class WorkflowConfig:
    def __init__(self, n, s, g):
        self.name = n
        self.states = s
        self.num_states = len(s)
        self.next_states = [list(i) for i in g]
        #self.pairs = self.transition_pairs_from_table()

    @classmethod
    def from_yaml(cls, y):
        definition = yaml.load(y)
        workflows = []

        for k,v in definition.items():
            states = {}
            for s in v['states']:
                state = {
                    'key': s['key'], 
                    'label': s['label']
                }

                if 'manual' in s and s['manual'] is True:
                    state['manual'] = True
                else:
                    state['manual'] = False

                if 'workflow' in s and s['workflow'] is True:
                    state['workflow'] = True
                else:
                    state['workflow'] = False

                if 'class' in s and s['class'] is True:
                    state['class'] = s['class']
                else:
                    state['class'] = None

                states[s['key']] = state

            workflows.append(cls(k,
                                 states,
                                 v['graph']))

        return workflows

    @classmethod
    def from_yaml_file(cls, path):
        with open(path, 'r') as f:
            return cls.from_yaml(f)


if "__main__" == __name__:
    l = WorkflowConfig.from_yaml_file('/local1/git/blue_sky_workflow_engine/workflow_engine/test/states.yml')

    for i in l:
        print(i.name)
        print(i.states)
        print(i.transitions)
        print(i.pairs)

