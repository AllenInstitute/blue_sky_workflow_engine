class InputConfigMixin(object):
    def get_workflow_node_input_template(self, task, name=None):
        '''May be used to read a :class:`~workflow_engine.models.configuration.Configuration`
        template from the database as a basis for a
        :class:`~workflow_engine.strategies.execution_strategy.ExecutionStrategy`
        input json.

        Args:
            task (Task) a :class:`~workflow_engine.models.task.Task` associated
            with a :class:`~workflow_engine.models.workflow_node.WorkflowNode`

        Returns:
            dict: a nested dict that may be further filled in by a strategy.
        '''
        workflow_node = task.job.workflow_node
        if name:
            input_config_name = name
        else:
            input_config_name = str(workflow_node) + ' Input'

        inp = workflow_node.configurations.get(
            name=input_config_name,
            configuration_type='strategy_config').json_object

        return inp
