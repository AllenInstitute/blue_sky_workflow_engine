# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2017. Allen Institute. All rights reserved.
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
from workflow_engine.import_class import import_class
import celery
import logging
import traceback


_log = logging.getLogger('workflow_engine.process.workers.ingest_tasks')


app = celery.Celery(
    'workflow_engine.process.workers.ingest_tasks'
)
configure_worker_app(app, settings.APP_PACKAGE, 'ingest')


def load_workflow_config(yaml_file):
    from workflow_engine.workflow_config import WorkflowConfig

    workflow_config = WorkflowConfig.from_yaml_file(yaml_file)

    return { 
        workflow_spec.name: workflow_spec.state_list
        for workflow_spec in workflow_config['flows']
    }


@celery.shared_task(bind=True)
def ingest_task(self, workflow, message, tags):
    '''Receive the ingest message, look up the strategy class and
    call its ingest_message method.

    Parameters
    ----------
    workflow : String
        the key of the workflow in the configuration yaml file
    message : dict
        the body of the ingest message
    tags : array of Strings
        additional flags that may be used to modify ingest behavior

    Returns
    -------
    dict or String
        response message body to be sent to the sender process
    '''
    from workflow_engine.models import Workflow

    ret = 'OK'

    try:
        _log.info('ingest ' + str(workflow) + ' ' + str(message))

        workflow_object = Workflow.objects.get(
            name=workflow)
        strategy_class = import_class(
            workflow_object.ingest_strategy_class)
        ingest_strategy = strategy_class()

        # TODO: use Celery router to call directly
        ret = ingest_strategy.ingest_message(
            workflow,
            message,
            tags)
#         self.update_state(state="SUCCESS",
#                           meta=ret)
    except Exception as e:
#         self.update_state(state="FAILURE")
        mess = str(e) + ' - ' + str(traceback.format_exc())
        _log.error(mess)
        ret = "FAIL " + mess

    return ret
