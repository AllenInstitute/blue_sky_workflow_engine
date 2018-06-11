Configuration Objects
=====================

This guide is a resource for using the Blue Sky Workflow Engine package.
It is maintained by the `Allen Institute for Brain Science <http://www.alleninstitute.org/>`_.

The Blue Sky Workflow Engine is designed for creating new workflows
to manage and orchestrate projects.


Introduction
------------

Configuration objects are 'blobs' of JSON stored in the Django model database with a GenericRelation association to other modeled objects. They are intended to be similar to WellKnownFile objects in behavior. They are flexible and can be used in several different contexts.


Editing Using the Admin UI
--------------------------

In the Django admin console, under workflow_engine, either create or edit
a configuration object.  Set the 'Content type' to the type of model you want
to associate to this JSON object.  Set the 'Object id' field to the id of
the object you want to associate. The name field will show up in list views
and the 'Configuration type' is a string that can be used
to query or filter configurations.

The 'Json object' field can be arbitrary JSON. Some syntax checking is done
by the UI, but no schema or other validation will be done by the admin UI.

Creating a Configuation Object using Python
-------------------------------------------

A configuration object is assigned to an object using the content_object 
`generic foreign key <https://docs.djangoproject.com/en/2.0/ref/contrib/contenttypes/#django.contrib.contenttypes.fields.GenericForeignKey>`_.

.. code-block:: python

    from workflow_engine.workflow_config import WorkflowConfig
    from workflow_engine.models.workflow_node import WorkflowNode

    node = WorkflowNode.objects.first()

    json_dict = {
        'this': 'that'
    }

    config = Configuration(
        content_object=node,
        name='Test Configuration',
        configuration_type='Example Configuration',
        json_object=json_dict)
    config.save()

Accessing a Configuration Object
--------------------------------

A 
`generic relation <https://docs.djangoproject.com/en/2.0/ref/contrib/contenttypes/#generic-relations>`_.
can be used to access a configuration directly from its associated object.

.. code-block:: python

    from django.contrib.contenttypes.fields import GenericRelation

    class WorkflowNode(models.Model):
        ...
        configurations = GenericRelation('workflow_engine.Configuration')

Then the configuration objects associated with a workflow node can be accessed
using the configurations attribute.

.. code-block:: python

    downsample_configs = node.configurations.filter(
        configuration_type='Example Configuration')

Configuration objects can also be queried directly. This can be useful for storing strategy default values.

.. code-block:: python

    inp = Configuration.objects.get(
        name='Apply Lens Correction Input',
        configuration_type='strategy_config').json_object
