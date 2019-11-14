Developers Guide
================

This guide is a resource for using the Blue Sky Workflow Engine package.
It is maintained by the `Allen Institute for Brain Science <http://www.alleninstitute.org/>`_.

The Blue Sky Workflow Engine uses a Celery Task Queue with a RabbitMQ broker to
manage job submissions to a Portable Batch System (PBS) job scheduler.
It organizes job queues using a workflow graph and a Django PostgreSQL database model to
store information about the equeued objects. The Django Admin plugin provides user interface features.

Support features include a PyTest test suite, code coverage using flake8, Sphinx Documentation,
Pip packaging and a Docker build.

Celery Task Queue and RabbitMQ Broker
-------------------------------------

 * `Celery <http://www.celeryproject.org/>`_
 * `RabbitMQ <https://www.rabbitmq.com/>`_

 * `Using Celery with Django <http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html>`_
 * `Celery Routing <http://docs.celeryproject.org/en/latest/userguide/routing.html>`_
 * `Celery Workflows with Canvas chains <http://docs.celeryproject.org/en/latest/userguide/canvas.html#chains>`_

 * `Flower Monitor <http://flower.readthedocs.io/en/latest/>`_
 * `RabbitMQ Management <https://www.rabbitmq.com/management.html>`_

Django Web Framework and Admin Plugin
-------------------------------------

 * `Django <https://www.djangoproject.com/>`_
 * `Admin Plugin <https://docs.djangoproject.com/en/2.0/ref/contrib/admin/actions/>`_


Optional Dependencies
---------------------

 * `pytest <http://pytest.org/latest>`_
 * `coverage <http://nedbatchelder.com/code/coverage>`_

