#!/bin/bash
export PYTHONPATH=/home/timf/at_em_imaging_workflow:/home/timf/blue_sky_workflow_engine:/home/timf/render-deploy/render_modules
export BLUE_SKY_SETTINGS=/data/aibstemp/timf/example_data/blue_sky_settings.yml
python -m workflow_client.celery_ingest "lens_correction_new" "this is a test"
sleep 10
python -m workflow_client.celery_ingest "em_2d_montage_point_match" "this is a test"
#sleep 10
#python -m workflow_client.celery_ingest "em_2d_montage" "this is a test"
#sleep 10
#python -m workflow_client.celery_ingest "at_2d_montage" "this is a test"
