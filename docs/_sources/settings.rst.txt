Settings
========

This guide is a resource for using the Blue Sky Workflow Engine package.
It is maintained by the `Allen Institute for Brain Science <http://www.alleninstitute.org/>`_.

The Blue Sky Workflow Engine is essentially an integration package.
The settings are an important part of that integration.


Celery Task Queue and RabbitMQ Broker Settings
----------------------------------------------

 * blue_sky_settings.yml
 * workflow_config.yml
 * DJANGO_SETTINGS_MODULE - settings.py
 * Moab credentials
 * Mounting writable volumes in Docker


Restarting the Worker Processes
-------------------------------

cd /at_em_imaging_workflow
./restart_processes.sh


Restarting the Docker Container
-------------------------------

This is necessary if you edit a volume-mounted file (for example settings.py)


Applying Database Migrations
----------------------------

cd /at_em_imaging_workflow
python -m manage showmigrations
python -m manage migrate


Django Shell
------------

cd /at_em_imaging_workflow
django-admin shell


Restoring a Nightly Backup Database
-----------------------------------

# backups are stored at /allen/ai/sqlbkup/vol_assem
# delete all existing data
django-admin flush
# using the postgres command line tool
pg_restore -n public -v -U <db username> -h <db host> -p <db port> -d vol_assem /allen/ai/sqlbkup/vol/assem/vol_assem_pg_20180307_2247



