.. _migrations:


Introduction
------------

Configuration objects are 'blobs' of JSON stored in the Django model database with a GenericRelation association to other modeled objects. They are intended to be similar to WellKnownFile objects in behavior. They are flexible and can be used in several different contexts.


Django Migrations
=================

See https://docs.djangoproject.com/en/2.2/topics/migrations/

Invoking Manager
================

python -m workflow_engine.management.manager showmigrations
Also makemigrations, migrate, up, down


Data Migrations and Why No Datafixes
====================================

See https://docs.djangoproject.com/en/2.2/topics/migrations/#data-migrations
