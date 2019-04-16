class InputConfigMixin(object):
    def get_workflow_node_input_template(self, task, name=None):
        workflow_node = task.job.workflow_node
        if name:
            input_config_name = name
        else:
            input_config_name = str(workflow_node) + ' Input'

        inp = workflow_node.configurations.get(
            name=input_config_name,
            configuration_type='strategy_config').json_object

        return inp
