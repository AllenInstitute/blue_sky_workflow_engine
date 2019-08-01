#!/bin/bash

APP=$1
ENV=$2
BG=$3
ln -s /blue_sky_workflow_engine/blue_green/restart_workers.sh /blue_green/restart_workers.sh
ln -s /blue_sky_workflow_engine/blue_green/process_manager.py /blue_green/process_manager.py
ln -s /${APP} /${BG}/${APP}
ln -s /blue_sky_workflow_engine /${BG}/blue_sky_workflow_engine
ln -s /${APP}/${APP}/settings.py /${BG}/settings.py
ln -s /allen/aibs/pipeline/image_processing/volume_assembly/workflow_conf/${ENV}/blue_sky_settings.yml /${BG}/blue_sky_settings.yml
