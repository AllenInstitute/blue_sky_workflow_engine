# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2018-2021. Allen Institute. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Redistributions for commercial purposes are not permitted without the
# Allen Institute's written permission.
# For purposes of this license, commercial purposes is the incorporation of the
# Allen Institute's software into anything for which you will charge fees or
# other compensation. Contact terms@alleninstitute.org for commercial licensing
# opportunities.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
import django; django.setup()
from django.conf import settings
from workflow_engine.client_settings import configure_worker_app
from workflow_engine.process.workers.moab_api import (
    submit_job,
    submit_job_array,
    delete_moab_task
)
from workflow_engine.signatures import (
    process_failed_execution_signature,
    process_pbs_id_signature
)
from django.core.exceptions import ObjectDoesNotExist
from workflow_engine.pbs_utils import PbsUtils
import celery
import logging
import traceback
import os


_log = logging.getLogger('workflow_engine.process.workers.moab_tasks')


app = celery.Celery('workflow_engine.process.workers.moab_tasks')
configure_worker_app(app, settings.APP_PACKAGE, 'moab')
# app.conf.imports = ()


@celery.shared_task(bind=True, trail=True)
def submit_moab_task(self, task_id):
    _log.info('Submitting task %d', task_id)

    try:
        the_task = Task.objects.get(id=task_id)

        the_strategy = the_task.get_strategy()
        pbs_file = the_strategy.get_pbs_file(the_task)
        the_task.create_pbs_file(pbs_file)

        if the_task.in_pending_state():
            _log.info('in pending state')

            try:
                moab_cfg = Configuration.objects.get(
                    configuration_type='moab_configuration').json_object
            except:
                moab_cfg = None

            remote_queue = the_task.get_executable().remote_queue

            if remote_queue == 'spark_moab':
                #Log4j
                log_dir = the_strategy.get_or_create_task_storage_directory(the_task)
                log4j_properties_path = os.path.join(log_dir, 'log4j.properties')
                # log4j_log_path = os.path.join(log_dir, 'spark.log')
                log4j_log_path = 'spark.log'

                PbsUtils().write_spark_log_files(
                    log4j_properties_path,
                    log4j_log_path
                )

                moab_id = submit_job_array(
                    the_task.id,
                    the_task.pbs_file,
                    moab_cfg=moab_cfg)
            elif remote_queue == 'slurm':
                slurm = SlurmApi()

                slurm_script = PbsUtils().get_template(
                    the_task.get_executable(),
                    the_task,
                    settings
                )

                moab_id = slurm.submit_job(
                    the_task.id,
                    os.path.dirname(the_task.pbs_file),
                    slurm_script
                )

            if moab_id != 'ERROR':
                # the_task.set_queued_state(moab_id)
                process_pbs_id_signature.delay(
                    task_id, moab_id)
            else:
                process_failed_execution_signature.delay(
                    task_id,
                    fail_now=True
                )
            else:
                moab_id = submit_job(
                    the_task.id,
                    the_task.pbs_file,
                    moab_cfg=moab_cfg)

            if moab_id != 'ERROR':
                # the_task.set_queued_state(moab_id)
                process_pbs_id_signature.delay(
                    task_id, moab_id)
            else:
                process_failed_execution_signature.delay(
                    task_id,
                    fail_now=True
                )

            _log.info("MOAB ID: {}".format(moab_id))
    except Exception as e:
        moab_id = None
        msg = 'Error submitting task {}'.format(str(e) + str(traceback.format_exc()))
        _log.error(msg)
        process_failed_execution_signature.delay(
            task_id,
            error_message=str(e),
            fail_now=True)


# TODO: change name to something like process task state
# Not sure if we still need name
# Do need a UI task like this
@celery.shared_task(bind=True)
def run_task(self, name, args):
    raise Exception("Removed/Unimplemented")


@celery.shared_task(bind=True, trail=True)
def kill_moab_task(self, task_id):
    response_message = 'killed'

    try:
        the_task = Task.objects.get(id=task_id)

        remote_queue = the_task.get_executable().remote_queue

        if remote_queue in ['spark_moab', 'pbs']:
            delete_moab_task(the_task.pbs_id)
        elif remote_queue == 'slurm':
                slurm = SlurmApi()
                slurm.delete_slurm_task(the_task.pbs_id)

        the_task.set_process_killed_state()  # TODO: rename for task/process
        response_message = str(the_task.pbs_id)
    except ObjectDoesNotExist as e:
        _log.warning("Cannot kill task %s, does not exist. %s",
                     task_id,
                     str(e))
        response_message = 'str(e)'

    return response_message

# circular imports
from workflow_engine.models import (
    Task,
    Configuration
)

