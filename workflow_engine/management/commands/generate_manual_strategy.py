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
            strategy_file.write('  #called before the task starts running\n')
            strategy_file.write('  #def prep_task(self, task):\n')
            strategy_file.write('  #    pass\n\n')

            strategy_file.write('  #override if needed\n')
            strategy_file.write('  #called if the task fails\n')
            strategy_file.write('  #def on_failure(self, task):\n')
            strategy_file.write('  #  pass\n\n')

            strategy_file.write('  #override if needed\n')
            strategy_file.write('  #called when the task starts running\n')
            strategy_file.write('  #def on_running(self, task):\n')
            strategy_file.write('  #  pass\n\n')
            

    def handle(self, *args, **options):
        name = options['name']

        strategy_directory = self.get_strategy_directory()
        filename = self.get_filename(strategy_directory, name)
        class_name = self.get_class_name(name)

        if os.path.exists(filename):
            raise Exception('Trying to write strategy file but file already exists at: ' + str(filename))

        self.write_strategy_file(filename, class_name)