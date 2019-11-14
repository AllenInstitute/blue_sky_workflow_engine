Install Guide
=============

This guide is a resource for using the Blue Sky Workflow Engine package.
It is maintained by the `Allen Institute for Brain Science <http://www.alleninstitute.org/>`_.

The Allen SDK was developed and tested with Python 3.6, installed.
We do not guarantee consistent behavior with other Python versions.

Quick Start Using Pip
---------------------

First ensure you have `pip <http://pypi.python.org/pypi/pip>`_ installed.
It is included with the Anaconda distribution.

::

    pip install blue_sky_workflow_engine


To uninstall::

    pip uninstall blue_sky_workflow_engine

Other Distribution Formats
--------------------------

The Allen SDK is also available from the Github source repository.

Required Dependencies
---------------------

 * Django
 * Celery
 * Pika

Optional Dependencies
---------------------

 * `pytest <http://pytest.org/latest>`_
 * `coverage <http://nedbatchelder.com/code/coverage>`_

Installation with Docker (Optional)
-----------------------------------

`Docker <http://www.docker.com/>`_ is an open-source technology
for building and deploying applications with a consistent environment
including required dependencies.
The AllenSDK is not distributed as a Docker image, but
example Dockerfiles are available.

 #. Ensure you have Docker installed.

 #. Use Docker to build one of the images.
 
     Anaconda::

         docker pull alleninstitute/blue_sky
 
     Other docker configurations are also available under docker directory in the source repository.
 
 #. Run the docker image::
 
     docker run -i -t alleninstitute/blue_sky /bin/bash
     cd blue_sky_workflow_engine
     make test
