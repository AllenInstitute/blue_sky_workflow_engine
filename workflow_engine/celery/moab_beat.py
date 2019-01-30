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
import celery
from django.conf import settings
import django; django.setup()
import logging.config
from workflow_client.client_settings import configure_worker_app
from workflow_engine.celery.signatures import (
    check_moab_status_signature,
    check_circus_task_status_signature,
    update_dashboard_signature
)


app = celery.Celery('workflow_engine.celery.moab_beat')
configure_worker_app(app, settings.APP_PACKAGE)
app.conf.imports = ('workflow_engine.celery.moab_tasks',)


# see: https://github.com/celery/celery/issues/3589
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    try:
        moab_check_seconds = settings.MOAB_CHECK_SECONDS
    except:
        moab_check_seconds = 45000.0

    try:
        dashboard_update_seconds = settings.DASHBOARD_UPDATE_SECONDS
    except:
        dashboard_update_seconds = 15.0

    sender.add_periodic_task(
        moab_check_seconds,
        check_moab_status_signature)
    sender.add_periodic_task(
        moab_check_seconds,
        check_circus_task_status_signature)
    sender.add_periodic_task(
        dashboard_update_seconds,
        update_dashboard_signature)


@celery.signals.after_setup_task_logger.connect
def after_setup_celery_task_logger(logger, **kwargs):
    """ This function sets the 'celery.task' logger handler and formatter """
    logging.config.dictConfig(settings.LOGGING)
