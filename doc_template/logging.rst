.. _logging:


Introduction
------------

Logging is on a worker by worker basis, as well as in test,
and management commands  


Python Logging
==============

See: https://docs.python.org/3.7/howto/logging.html

Logging Configuration with Celery and Django
============================================

See: https://stackoverflow.com/questions/48289809/celery-logger-configuration


Logging from a Module
=====================

How to define a logger and send log messages.


Changing Log Levels, Formatters, etc. in the Django Setting Module
==================================================================

Show example from a settings file.

Known Issues
============

Most of the worker logs stop logging after the celery worker gets launched,
so they aren't informative in practice.
