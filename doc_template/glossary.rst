Glossary
--------

.. glossary::

    celery task
        a message handler

    configuration
        a databased json object optionally associated with an object that uses
        the configurable mixin.
    
    enqueued object
        a database object that can be directly assigned to workflow jobs.

    flower
        a tool to monitor celery messaging.

    finite state machine
        an abstraction defined by states and transitions between states.
        The django_fsm package is used to implement workflow and object
        state transitions in the workflow engine.

    job
        a specific enqueued object running on a workflow node.

    object state
        an optional field on an application model to track state using a
        finite state machine

    strategy
        a python module that creates and handles a job's input and output and
        updates the database with respect to a specific enqueued object. 

    storage directory
        a path specific to an enqueued object or task that may be used by a strategy.

    task
        a job may run as one or more tasks on a compute cluster.
        Blue sky tasks are a distinct concept from celery messaging tasks.

    well known file
        a databased representation of an external file associated with an object
        that uses the has_well_known_file mixin.

    workflow
        a series of manual or automated processing steps with a dependency relationship

    workflow node
        one processing step for an enqueued object in a workflow

    workflow state
        the state of a job or task that may be run on a compute cluster
        PENDING, QUEUED,RUNNING, FINISHED_EXECUTION, SUCCESS, FAILED,
        FAILED_EXECUTION and PROCESS_KILLED are possible states.
