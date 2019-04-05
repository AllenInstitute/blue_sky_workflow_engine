#!/bin/bash

pkill -9 -f "flower"
pkill -9 -f "circus"
pkill -9 -f "ui_server"
pkill -9 -f "beat"
pkill -9 -f "manage"
pkill -9 -f "notebook"

# make sure MOAB_AUTH is defined

export BG=green
export APP=$1
export BG_CONDA_ENV=base
export BG_CIRCUS_ENV=circus
export BASE_DIR=/${BG}/$APP
export PYTHONPATH=/blue_green:${BASE_DIR}:/${BG}/blue_sky_workflow_engine:$PYTHONPATH

rm ${BASE_DIR}/logs/ingest.log
rm ${BASE_DIR}/logs/ui.log
rm ${BASE_DIR}/logs/moab.log
rm ${BASE_DIR}/logs/moab_status.log
rm ${BASE_DIR}/logs/monitor.log
rm ${BASE_DIR}/logs/workflow.log
rm ${BASE_DIR}/logs/local.log
rm ${BASE_DIR}/logs/circus.log
rm ${BASE_DIR}/logs/result.log
rm ${BASE_DIR}/logs/beat.log
rm celerybeat.pid

unset DJANGO_SETTINGS_MODULE

source activate ${BG_CONDA_ENV}

#echo 'STARTING CIRCUSD'
#/bin/bash -c 'source activate circus; cd /blue_sky_workflow_engine/circus; /opt/conda/envs/circus/bin/circusd --daemon circus.ini'

echo CONDA ENV: ${BG_CIRCUS_ENV}
echo PYTHONPATH: ${PYTHONPATH}
/bin/bash -c 'source activate ${BG_CIRCUS_ENV}; python -m process_manager  ${APP} ${BG}'

