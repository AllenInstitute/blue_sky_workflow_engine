#!/bin/bash
export APP_NAME=at_em_imaging_workflow
export MESSAGE_QUEUE_HOST=ibs-timf-ux1.corp.alleninstitute.org
export PYTHONPATH=/home/timf/at_em_imaging_workflow:/home/timf/blue_sky_workflow_engine:/home/timf/render_modules
export BLUE_SKY_SETTINGS=/data/aibstemp/timf/example_data/blue_sky_settings.yml
python -m celery flower --backend=rpc:// --broker=amqp://blue_sky_user:blue_sky_user@${MESSAGE_QUEUE_HOST}:5672 -n flower@${APP_NAME} --pidfile=celery.pid&
python -m celery -A workflow_client.celery_ingest_consumer worker --loglevel=debug --concurrency=2 -Q ingest -n ingest@${APP_NAME} --pidfile=ingest.pid 2>&1 | tee ingest.log&
python -m celery -A workflow_client.celery_ingest_consumer worker --loglevel=debug --concurrency=2 -Q pbs -n pbs@${APP_NAME} --pidfile=pbs.pid 2>&1 | tee ingest.log&
python -m celery -A workflow_client.celery_ingest_consumer worker --loglevel=debug --concurrency=2 -Q result,null -n result@${APP_NAME} --pidfile=result.pid 2>&1 | tee server.log&
