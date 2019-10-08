#!/bin/bash

pkill -9 -f "flower"
pkill -9 -f "workflow_engine.process.process_manager"
pkill -9 -f "ui_server"
pkill -9 -f "beat"
pkill -9 -f "manage"
pkill -9 -f "notebook"

# make sure MOAB_AUTH is defined

export APP=$1
export WORKDIR=/home/blue_sky_user/work
export BG_CIRCUS_ENV=/conda_envs/circus
export LOG_DIR=${WORKDIR}/logs

rm ${LOG_DIR}/*.log
rm celerybeat.pid

#unset DJANGO_SETTINGS_MODULE

echo CONDA ENV: ${BG_CIRCUS_ENV}
echo PYTHONPATH: ${PYTHONPATH}
/bin/bash -c 'source activate ${BG_CIRCUS_ENV}; python -m workflow_engine.process.process_manager ${APP} ${WORKDIR}'

