#!/bin/bash
#SBATCH -p {{ executable.pbs_queue }}
{% for p in executable.pbs_processor.split(':') -%}
#SBATCH {{ p }}
{% endfor -%} 
#SBATCH --time {{ executable.pbs_walltime.split('=')[-1] }}
#SBATCH --job-name {{ task.get_task_name() }}
#SBATCH -o {{ task.log_file }}

function finish {
    source activate {{ settings.PBS_RESPONSE_CONDA_ENV }}
    python -m workflow_engine.mini_response --action finished {{ task.id }} --app-name {{ settings.APP_PACKAGE }}
}

trap finish TERM
trap finish EXIT

source /etc/profile
module load anaconda

export TMPDIR="/scratch/capacity/${SLURM_JOBID}/"
export SPARK_LOCAL_DIRS="/scratch/capacity/${SLURM_JOBID}/"
export PYTHONNOUSERSITE=1
export BLUE_SKY_SETTINGS={{ settings.BLUE_SKY_SETTINGS_HPC_RESPONSE }}
{% for evar in task.environment_vars() -%}
export {{ evar }}
{% endfor -%}

export PYTHONPATH=${PYTHONPATH}:{{ settings.HPC_RESPONSE_PYTHONPATH }}

umask 002

source activate {{ settings.PBS_RESPONSE_CONDA_ENV }}
python -m workflow_engine.mini_response --action running {{ task.id }} --app-name {{ settings.APP_PACKAGE }}

source activate {{ settings.PBS_CONDA_ENV }}
{{ task.full_executable }}
