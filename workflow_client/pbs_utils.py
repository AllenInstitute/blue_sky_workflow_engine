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
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTuWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
import jinja2

class PbsUtils(object):
    def __init__(self):
        self.package = 'workflow_client'
        self.templates = 'templates'
        self.scripts = {
            'spark_moab': 'spark_submit_cluster.pbs',
            # 'spark': 'spark_submit_cluster.pbs',
            'circus': 'script_template.pbs',
            'pbs': 'script_template.pbs',
            'default': 'script_template.pbs'
        }

    def get_template(self, executable, task, settings):
        env = jinja2.Environment(
           loader=jinja2.PackageLoader(
               self.package, self.templates))

        script_key = executable.remote_queue
        if not script_key in self.scripts:
            script_key = 'default'

        pbs_template = env.get_template(
            self.scripts[script_key]
        )

        task_strategy = task.job.workflow_node.get_strategy()
        task_storage_directory = task_strategy.get_task_storage_directory(task)

        return pbs_template.render(
            executable=executable,
            task=task,
            settings=settings,
            task_storage_directory=task_storage_directory)
