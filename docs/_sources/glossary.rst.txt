Glossary
--------

.. glossary::

    configuration
        a databased json object optionally associated with an object that uses
        the configurable mixin.
    
    enqueued object
        a database object that can be directly assigned to workflow jobs.
    
    job
        a specific enqueued object running on a workflow node.
    
    strategy
        a python module that creates and handles a job's input and output and
        updates the database with respect to a specific enqueued object. 
    
    storage directory
        a path specific to an enqueued object or task that may be used by a strategy.
    
    task
        a job may run as one or more tasks on a compute cluster
    
    well known file
        a databased representation of an external file associated with an object
        that uses the has_well_known_file mixin.
    
    workflow
        a series of manual or automated processing steps with a dependency relationship
    
    workflow node
        one processing step for an enqueued object in a workflow
