# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2018-2019. Allen Institute. All rights reserved.
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
from workflow_engine.signatures import (
    process_pbs_id_signature,
    process_running_signature,
    process_failed_execution_signature,
    process_finished_execution_signature
)
import celery
import logging
import os


_log = logging.getLogger('workflow_engine.celery.local_tasks')

app = celery.Celery('workflow_engine.celery.local_tasks')
configure_worker_app(app, settings.APP_PACKAGE, 'local')


SUCCESS_EXIT_CODE = 0
ERROR_EXIT_CODE = 1


def query_running_task_dicts():
    #tasks = Task.objects.filter(
    #    running_state__in=['QUEUED', 'RUNNING'])

    task_dicts = []

    _log.info('task dicts unimplemented')

    return task_dicts


@celery.shared_task(bind=True, trail=True)
def check_status(self):
    return 'OK'


@celery.shared_task(bind=True, trail=True)
def submit_worker_task(self, task_id):
    _log.info('Submitting task %d', task_id)

    try:
        the_task = Task.objects.get(id=task_id)

        if the_task.in_pending_state():
            process_pbs_id_signature.delay(task_id, None)
            process_running_signature.delay(task_id)

            exit_code = os.system(the_task.full_executable)

            if exit_code == SUCCESS_EXIT_CODE:
                process_finished_execution_signature.delay(task_id)

                # with open(logfile, "a") as log:
                #     log.write("SUCCESS - execution finished successfully for task " +
                #     str(task_id))
            else:
                process_failed_execution_signature.delay(task_id)

                # with open(logfile, "a") as log:
                #    log.write("FAILURE - execution failed for task " + str(task_id))
    except:
        process_failed_execution_signature.delay(task_id)

    return None


# TODO: change name to something like process task state
# Not sure if we still need name
# Do need a UI task like this
@celery.shared_task(bind=True)
def run_task(self, name, args):
    raise Exception("Removed/Unimplemented")


@celery.shared_task(bind=True, trail=True)
def kill_task(self, task_id):
    raise Exception("Removed/Unimplemented")

# circular imports
from workflow_engine.models import Task
