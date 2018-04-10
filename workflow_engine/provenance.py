import yaml
from django.conf import settings
from workflow_client import client_settings
import copy
import logging


class Provenance(object):

    def __init__(self):
        self.json_dict = dict()

    def record_pip_freeze_dependencies(
        self, environment_name, file_path):
        pass

    def read_pip_freeze_dependencies(
        self, file_path):
        with open(file_path,'r') as f:
            deps = []
            for l in f.readlines():
                try:
                    package,version = l.strip().split('==')
                    entry = { 'name': package }
                    version_numbers = version.split('.')
                    if len(version_numbers) == 3:
                        entry['version'] = {
                            'major': version_numbers[0],
                            'minor': version_numbers[1],
                            'patch': version_numbers[2]
                        }
                    elif len(version_numbers) == 2:
                        entry['version'] = {
                            'major': version_numbers[0],
                            'minor': version_numbers[1],
                        }
                    deps.append(entry)
                except:
                    pass

        self.json_dict['pip'] = deps

    def record_blue_sky_configuration(
        self, blue_sky_configuration_file):

        conf = client_settings.load_settings_yaml()

        self.json_dict['blue_sky'] = conf

    def record_django_settings(self, keys):
        self.json_dict['django'] = dict()

        for k in keys:
            self.json_dict['django'][k] = \
                copy.deepcopy(settings.__getattr__(k))

    def record_executable_configuration(self):
        pass

    def record_workflow_configuration(self, yaml_file):
        with open(yaml_file, 'r') as f:
            definition = yaml.load(f)

        self.json_dict['workflow'] = definition

    def record_job_execution(self):
        pass