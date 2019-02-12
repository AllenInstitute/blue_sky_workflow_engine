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
from workflow_engine.models import WellKnownFile
from django.conf import settings
import subprocess
import logging
import traceback
import os


class BaseStrategy(object):
    _log = logging.getLogger('workflow_engine.strategies.base_strategy')
    # 
    # everthing bellow this can be overriden
    #

    # override if needed
    # called before the job starts running
    def prep_job(self, job):
        pass

    # override if needed
    # called before the task starts running
    def prep_task(self, task):
        pass

    # override if needed
    # called if the task fails
    def on_failure(self, task):
        pass

    # override if needed
    # called when the task starts running
    def on_running(self, task):
        pass

    # override if needed
    # called after the execution finishes
    # process and save results to the database
    def on_finishing(self, enqueued_object, results, task):
        pass

    # override if needed
    def get_storage_directory(self, base_storage_directory, job):
        enqueued_object = job.get_enqueued_object()
        BaseStrategy._log.info('get_storage_directory: %s, %s:' % (
            base_storage_directory, str(enqueued_object.id)))
        return os.path.join(
            base_storage_directory,
            # str(job.enqueued_object_type),
            str(job.enqueued_object_id))

    # override if needed
    # this is called when a job is transitioning from a previous queue
    # given the previous job, return an array of enqueued objects
    # for this queue
    def get_objects_for_queue(self, prev_queue_job):
        objects = []
        objects.append(prev_queue_job.get_enqueued_object())
        return objects

    # override if needed
    # return one or more task enqueued objects for a job enqueued object
    def get_task_objects_for_queue(self, enqueued_object):
        objects = []
        objects.append(enqueued_object)

        return objects

    # override if needed
    def can_transition(self, enqueued_object, workflow_node=None):
        return True

    #
    # everthing bellow this should not be overriden
    #

    # Do not override
    def get_base_storage_directory(self):
        return settings.BASE_FILE_PATH

    # Do not override
    def is_execution_strategy(self):
        return False

    def is_wait_strategy(self):
        return False

    # Do not override
    def get_job_storage_directory(self, base_storage_directory, job):
        return os.path.join(
            self.get_storage_directory(base_storage_directory, job),
            'jobs', 'job_' + str(job.id))

    @classmethod
    def make_dirs_chmod(cls, path, mode):
        if not path or os.path.exists(path):
            return []
        (head, _) = os.path.split(path)
        res = cls.make_dirs_chmod(head, mode)
        try:
            os.mkdir(path)
        except:
            pass
        # os.chmod(path, mode)
        res += [path]
        return res

    # Do not override
    def get_or_create_task_storage_directory(self, task):
        storage_directory = self.get_task_storage_directory(task)
        BaseStrategy.make_dirs_chmod(storage_directory, 0o777)

        return storage_directory

    # Do not override
    def check_key(self, dictionary, key):
        if key not in dictionary:
            raise Exception("expected '" + str(key) + "' key in results")

    # Do not override
    def get_or_create_storage_directory(self, job):
        storage_directory = self.get_job_storage_directory(
            self.get_base_storage_directory(), job)
        BaseStrategy.make_dirs_chmod(storage_directory, 0o777)

        return storage_directory

    # Do not override
    def fail_task(self, task):
        try:
            self.on_failure(task)
        except Exception as e:
            task.set_error_message(str(e) + ' - ' + \
                str(traceback.format_exc()))

        task.set_failed_state()
        task.set_end_run_time()
        task.job.set_failed_state()
        task.job.set_end_run_time()
        task.rerun()

    # Do not override
    def set_well_known_file(self, full_path, attachable_object,
                            well_known_file_type, task=None):
        # from workflow_engine.models import WellKnownFile
        WellKnownFile.set(full_path,
                          attachable_object,
                          well_known_file_type,
                          task)

    # Do not override
    def get_well_known_file(self, attachable_object, well_known_file_type):
        return WellKnownFile.get(attachable_object, well_known_file_type)
