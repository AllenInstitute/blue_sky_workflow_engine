#!/bin/bash

pkill -9 -f "flower"
pkill -9 -f "circus"
pkill -9 -f "ui_server"
pkill -9 -f "beat"
pkill -9 -f "manage"
pkill -9 -f "notebook"

# make sure MOAB_AUTH is defined

export APP=$1
export BG=$2
export BG_CONDA_ENV=/conda_envs/py_37
export BG_CIRCUS_ENV=/conda_envs/circus
export BASE_DIR=/${BG}/$APP
export PYTHONPATH=/blue_green:${BASE_DIR}:/${BG}/blue_sky_workflow_engine:$PYTHONPATH
export LOG_DIR=/logs

rm ${LOG_DIR}/ingest.log
rm ${LOG_DIR}/ui.log
rm ${LOG_DIR}/moab.log
rm ${LOG_DIR}/moab_status.log
rm ${LOG_DIR}/monitor.log
rm ${LOG_DIR}/workflow.log
rm ${LOG_DIR}/mock.log
rm ${LOG_DIR}/circus.log
rm ${LOG_DIR}/result.log
rm ${LOG_DIR}/beat.log
rm celerybeat.pid

unset DJANGO_SETTINGS_MODULE

source activate ${BG_CONDA_ENV}

#echo 'STARTING CIRCUSD'
#/bin/bash -c 'source activate circus; cd /blue_sky_workflow_engine/circus; /opt/conda/envs/circus/bin/circusd --daemon circus.ini'

echo CONDA ENV: ${BG_CIRCUS_ENV}
echo PYTHONPATH: ${PYTHONPATH}
/bin/bash -c 'source activate ${BG_CIRCUS_ENV}; python -m process_manager  ${APP} ${BG}'

