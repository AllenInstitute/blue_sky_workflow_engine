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
from django.core.management.base import BaseCommand, CommandError
from workflow_engine.models import Datafix
import os
import re

class Command(BaseCommand):
    help = 'Generate a manual Strategy - use snake_case for name arg'

    def add_arguments(self, parser):
        parser.add_argument('name')

    def get_strategy_directory(self):
        directory = Datafix.get_development_strategy_path()

        if not os.path.exists(directory):
            os.makedirs(directory)

        return directory

    def get_class_name(self, name):
        return name.title().replace('_', '') + 'Strategy'

    def to_underscore_case(self, name):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def get_filename(self, strategy_directory, name):
        return os.path.join(strategy_directory, self.to_underscore_case(name) + '_strategy.py')

    def write_strategy_file(self, filename, class_name):
        with open(filename, 'w') as strategy_file:
            strategy_file.write('from workflow_engine.strategies import manual_strategy\n')
            strategy_file.write('from workflow_engine.models import *\n')
            strategy_file.write('from development.models import *\n\n')
            strategy_file.write('class ' + class_name + '(manual_strategy.ManualStrategy):\n\n')

            strategy_file.write('  #override if needed\n')
            strategy_file.write('  #add code that returns true when a manual task is finished\n')
            strategy_file.write('  def task_finished(self, task):\n')
            strategy_file.write('    # enqueued_object = task.get_enqueued_object()\n')
            strategy_file.write('    return True\n\n')

            strategy_file.write('  #override if needed\n')
            strategy_file.write('  #called after the execution finishes\n')
            strategy_file.write('  #process and save results to the database\n')
            strategy_file.write('  def on_finishing(self, enqueued_object, results, task):\n')
            strategy_file.write('    pass\n\n')

            strategy_file.write('  #override if needed\n')
            strategy_file.write('  #this is called when a job is transitioning from a previous queue\n')
            strategy_file.write('  #given the previous job, return an array of enqueued objects for this queue\n')
            strategy_file.write('  #def get_objects_for_queue(self, prev_queue_job):\n')
            strategy_file.write('  #  objects = []\n')
            strategy_file.write('  #  objects.append(prev_queue_job.get_enqueued_object())\n')
            strategy_file.write('  #  return objects\n\n')

            strategy_file.write('  #override if needed\n')
            strategy_file.write('  #return one or more task enqueued objects for a job enqueued object\n')
            strategy_file.write('  #def get_task_objects_for_queue(self, enqueued_object):\n')
            strategy_file.write('  #  objects = []\n')
            strategy_file.write('  #  objects.append(enqueued_object)\n')
            strategy_file.write('  #  return objects\n\n')

            strategy_file.write('  #override if needed\n')
            strategy_file.write('  #set the storage directory for an enqueued object\n')
            strategy_file.write('  #def get_storage_directory(self, base_storage_directory, job):\n')
            strategy_file.write('  #  enqueued_object = job.get_enqueued_object()\n')
            strategy_file.write('  #  return os.path.join(base_storage_directory, str(enqueued_object.id))\n\n')

            strategy_file.write('  #override if needed\n')
            strategy_file.write('  #called before the job starts running\n')
            strategy_file.write('  #def prep_job(self, job):\n')
            strategy_file.write('  #  pass\n\n')

            strategy_file.write('  #override if needed\n')
            strategy_file.write('  #called before the task starts running\n')
            strategy_file.write('  #def prep_task(self, task):\n')
            strategy_file.write('  #  pass\n\n')

            strategy_file.write('  #override if needed\n')
            strategy_file.write('  #called if the task fails\n')
            strategy_file.write('  #def on_failure(self, task):\n')
            strategy_file.write('  #  pass\n\n')

            strategy_file.write('  #override if needed\n')
            strategy_file.write('  #called when the task starts running\n')
            strategy_file.write('  #def on_running(self, task):\n')
            strategy_file.write('  #  pass\n\n')

            strategy_file.write('  #override if needed\n')
            strategy_file.write('  #def can_transition(self, enqueued_object):\n')
            strategy_file.write('  #  return True\n')

    def handle(self, *args, **options):
        name = options['name']

        strategy_directory = self.get_strategy_directory()
        filename = self.get_filename(strategy_directory, name)
        class_name = self.get_class_name(name)

        if os.path.exists(filename):
            raise Exception('Trying to write strategy file but file already exists at: ' + str(filename))

        self.write_strategy_file(filename, class_name)