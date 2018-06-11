Strategies
==========

Introduction
~~~~~~~~~~~~

Execution Strategies
~~~~~~~~~~~~~~~~~~~~
Execution strategies query the model based on the enqueued object.
They create an input JSON file from a template configuration 
and the query results. They then create a PBS script, read the output json
and then store the results in the database and configuration objects.

A simple execution strategy can build an input.json from three sources.
The basic template can come from a Configuration object stored in the
database and associated with the strategies workflow node.
It can also be filtered by name and configuration_type as shown below.
The json template can then be filled in based on the settings object,
which is useful for values that vary by deployment.
Most often, additional values will come from
the enqueued object and its associated models.

The on_finishing method can check the output json, raise exceptions in the case of an unexpected or failed result, and update the enqueued object in the database

.. code-block:: python

    from workflow_engine.strategies.execution_strategy import ExecutionStrategy
    from workflow_engine.models.configuration import Configuration
    from django.conf import settings
    import copy

    class ExampleStrategy(ExecutionStrategy):
        def get_input(self, observation, storage_directory, task):
            strategy_configuration = \
                Configuration.objects.filter(
                    name='Apply Lens Correction Input',
                    configuration_type='strategy_config')
            # input.json template from database
            inp = copy.deepcopy(strategy_configuration.json_object)
    
            inp['arg1'] = settings.ARG_1  # from django settings
            inp['arg2'] = observation.measurement # from enqueued object

            return inp 

        def on_finishing(self, observation, results, task):
            self.check_key(results, 'result_value')
            observation.measurement = results['result_value']
            observation.save()


Wait Strategies
---------------

Wait strategies are used to hold an object unless and until an external
condition is met. They inherit from WaitStrategy and implement must_wait.
These can be used to hold an enqueued object for a manual quality control step
or to implement a barrier to wait for other objects to complete processing
before proceeding with following job queues. Note that wait strategy workflow
nodes usually have a mock executable as a place holder.
You can `add functionality to the admin UI <https://docs.djangoproject.com/en/1.11/ref/contrib/admin/actions/>`_
to allow the user to set or modify the state of a group of objects.

.. code-block:: python

    from workflow_engine.strategies.wait_strategy import WaitStrategy

    class WaitForLensCorrection(WaitStrategy):
        def must_wait(self, observation):
            # Use this to check if the reference set is available
            # return true if the state is correct
            manual_setting = observation.manual_setting
        
            if manual_setting is None:
                return True
    
            return False


Ingest Strategies
~~~~~~~~~~~~~~~~~

An ingest strategy is used to create or update an object from an external
message source. It is usually the first strategy in a workflow.
An ingest strategy does not run an executable module.

.. code-block:: yaml

    from django.conf import settings
    from workflow_engine.strategies.ingest_strategy import IngestStrategy
    from blue_sky.models.observation import Observation
    import logging

    class MockIngest(IngestStrategy):
        _log = logging.getLogger('blue-sky.mock_ingest')

        def get_workflow_name(self):
            return 'mock_workflow'

        def create_enqueued_object(self, message, tags=None):
            (obs, _) = Observation.objects.update_or_create(
                arg1 = message['arg1'],
                arg2 = message['arg2'],
                arg3 = message['arg3'],
                defaults={
                    'proc_state': 'PENDING'
                })

            return obs, None


        def generate_response(self, observation):
            return {
                'observation_id': observation.id
            }


