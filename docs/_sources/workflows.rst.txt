.. _workflows:

Workflows
=========

This guide is a resource for using the Blue Sky Workflow Engine package.
It is maintained by the `Allen Institute for Brain Science <http://www.alleninstitute.org/>`_.

The Blue Sky Workflow Engine is designed for creating new workflows
to manage and orchestrate projects.


Workflow YAML Format
--------------------

Workflows can be specified in a
`YAML <http://yaml.org/start.html>`_ syntax document.
A workflow file has three top-level sections: executables, run_states (deprecated) and workflows.


Executables
~~~~~~~~~~~

The pbs_processor and pbs_walltime entries are directives that are used in creating a `qsub <http://docs.adaptivecomputing.com/torque/3-0-5/commands/qsub.php>`_ script.


.. code-block:: yaml
   
    executables:
    
        mock:
            name: 'Mock Executable'
            path: '/path/to/bin/on/hpc/cluster/mock_executable'
            remote_queue: 'pbs'
            pbs_queue: 'project_queue_name'
            pbs_processor: 'nodes=1:ppn=1'
            pbs_walltime: 'walltime=0:10:00'

Run States
~~~~~~~~~~

.. note::

    The run_states section is deprecated. Leave it verbatim as below for now.

.. code-block:: yaml

    run_states:
        - "PENDING"
        - "QUEUED"
        - "RUNNING"
        - "FINISHED_EXECUTION"
        - "FAILED_EXECUTION"
        - "FAILED"
        - "SUCCESS"
        - "PROCESS_KILLED"


Workflows
~~~~~~~~~

The workflows section describes the JobQueue objects and their corresponding
WorkflowNode objects arranged in a Workflow object.

The workflows element has a sub element with a key for each workflow (in this case 'mock_workflow' is the only one). Under the workflow key is an optional 'ingest' strategy, a list of 'states' and a 'graph' of the relation between the states.

.. note::

    The 'states' roughly correspond to the JobQueue and WorkflowNode objects
    in the Django model. The graph represents the parent relationship between
    WorkflowNodes.

Each workflow has an 'ingest' element with the name of an ingest strategy.
The ingest strategy accepts a JSON message from an upstream client external to
the workflow and creates `Django model objects <https://docs.djangoproject.com/en/1.11/topics/db/>`_. For workflows that process objects that have already been created by another workflow or via the admin UI an ingest strategy is not needed.

The 'states' element contains a list of entries for JobQueues and WorkflowNodes. For each entry, a JobQueue will be created with the specified 'class', 'executable' and 'enqueued_class'

The 'graph' element contains a list of lists to specify the parent child relationship.  The 'key' of the parent node is followed by a list for the children.

.. warning::

    There are known issues with the graph representation.
    It is currently best to list the nodes roughly in order.
    Multiple parents cannot currently be represented,
    but the import code may not log an error.


.. code-block:: yaml

    workflows:
        mock_workflow:
            ingest: "blue_sky.strategies.mock_ingest.MockIngest"

            states:
                - key: "ingest_mock"
                  label: "Ingest Mock"
                  class: "blue_sky.strategies.mock_ingest.MockIngest"
                  enqueued_class: "blue_sky.models.observation.Observation"
                  executable: "mock"

                - key: "mock_analyze"
                  label: "Mock Analyze"
                  class: "blue_sky.strategies.mock_analyze.MockAnalyze"
                  enqueued_class: "blue_sky.models.observation.Observation"
                  executable: "mock"

            graph:
                - [ "ingest_mock", [ "mock_analyze" ] ]
 

Reloading the Workflow
----------------------

There is a 
`custom Django management command <https://docs.djangoproject.com/en/2.0/howto/custom-management-commands/>`_
for reloading the workflows from a yaml file.

::

    $ python -m manage import_workflows path/to/workflow_file.yml

.. warning::

    Reloading the workflows currently does a cascading delete on all
    job records.


Editing a Workflow in the Admin UI
----------------------------------

A job queue may be added to a workflow or modified using the Django Admin UI.
Under the workflow_engine section, first add  an executable.
Then add a job_queue that references the executable.
Finally add a workflow node. Assign it to a workflow and set the parent node.
You can then access the new node in the workflow view 
or on the workflow admin page.


.. note::
   There is currently no way to export a yaml file when the workflow
   has been edited using the admin UI.
