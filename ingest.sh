#!/bin/bash
export PYTHONPATH=/local1/git/at_em_imaging_workflow:/local1/git/blue_sky_workflow_engine:/local1/git/render-deploy/render_modules
#export BLUE_SKY_SETTINGS=/data/aibstemp/timf/example_data/blue_sky_settings.yml
export BLUE_SKY_SETTINGS=/allen/aibs/pipeline/image_processing/volume_assembly/workflow_conf/dev/blue_sky_settings.yml

python -m workflow_client.celery_ingest at_em_imaging_workflow em_2d_montage rendermodules.ingest.schemas.example ReferenceSet
python -m workflow_client.celery_ingest at_em_imaging_workflow em_2d_montage rendermodules.ingest.schemas.example EMMontageSet
#sleep 1
#python -m workflow_client.celery_ingest at_em_imaging_workflow em_2d_montage rendermodules.ingest.schemas.example EMMontageSet
#sleep 1
#python -m workflow_client.celery_ingest at_em_imaging_workflow em_2d_montage rendermodules.ingest.schemas.example EMMontageSet
#sleep 1

#python -m workflow_client.celery_ingest "em_2d_montage_point_match" "this is a test"

#sleep 10
#python -m workflow_client.celery_ingest "at_2d_montage" "this is a test"
