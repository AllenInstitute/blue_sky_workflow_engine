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
from django.db import models
from workflow_engine.mixins import (
    Archivable,
    Configurable,
    Nameable,
    Timestamped
)
import logging
_model_logger = logging.getLogger('workflow_engine.models.executable')


class Executable(Archivable, Configurable, Nameable, Timestamped, models.Model):
    static_arguments = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    environment = models.CharField(
        max_length=1000,
        null=True,
        blank=True
    )
    executable_path = models.CharField(
        max_length=1000
    )
    pbs_executable_path = models.CharField(
        max_length=1000,
        null=True,
        blank=True
    )
    remote_queue = models.CharField(
        max_length=255,
        default='pbs',
        blank=True
    )
    pbs_processor = models.CharField(
        max_length=255,
        default='vmem=6g',
        blank=True
    )
    pbs_walltime = models.CharField(
        max_length=255,
        default='walltime=5:00:00',
        blank=True
    )
    pbs_queue = models.CharField(
        max_length=255,
        default='lims',
        blank=True
    )
    version = models.CharField(
        max_length=255,
        default='0.1',
        blank=True
    )

    def get_job_queues(self):
        return self.jobqueue_set.all()

    def spark_moab_environment(self):
        # TODO: factor into a spark_moab helper class
        spark_cfgs =  self.configurations.filter(
            configuration_type='spark_moab_configuration'
        )

        num_spark_cfgs = spark_cfgs.count()

        if num_spark_cfgs == 1:
            spark_cfg = spark_cfgs.first()
            return spark_cfg.json_object
        elif num_spark_cfgs > 1:
            self.set_error_message(
                'Found {} not one spark configurations on {}'.format(
                    num_spark_cfgs,
                    self.name
                )
            )
            self.fail_task()

        return None



    def environment_vars(self):
        '''
            returns: environment variable list in form VAR=val
        '''
        env = self.environment
        _model_logger.info('ENV :{}'.format(env))

        if env is None or len(env) == 0:
            env = []
        else:
            try:
                env = env.split(';')
            except:
                env = []

        spark_env = self.spark_moab_environment()
        _model_logger.info('SPARK ENV: {}'.format(spark_env))

        if spark_env is not None:
            env.extend(["{}={}".format(k,v) for k,v in spark_env.items()])

        _model_logger.info("ENV: {}".format(env))

        return env
