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
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
import workflow_engine
import re
import os
import logging
_model_logger = logging.getLogger('workflow_engine.models')

class Datafix(models.Model):
    name = models.CharField(max_length=255)
    timestamp = models.CharField(max_length=255)
    run_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @staticmethod
    def get_extension(filename):
        try:
            extension = os.path.splitext(filename)[ONE]
        except:
            extension = ''

        return extension

    def get_workflow_path():
        return os.path.dirname(workflow_engine.__file__)

    def get_module_path(module):
        return os.path.dirname(module.__file__)

    @staticmethod
    def get_module_strategy_path(module):
        return os.path.join(Datafix.get_module_path(module),'strategies/')

    @staticmethod
    def get_workflow_datafix_path():
        return os.path.join(Datafix.get_workflow_path(),'datafixes/')

    @staticmethod
    def get_module_datafix_path(module):
        return os.path.join(Datafix.get_module_path(module),'datafixes/')

    @staticmethod
    def create_datafix_records_if_needed(module):
        workflow_datafix_dir = Datafix.get_workflow_datafix_path()
        dev_datafix_dir = Datafix.get_module_datafix_path(module)

        files = os.listdir(workflow_datafix_dir) + os.listdir(dev_datafix_dir)

        for file in files:
            if Datafix.get_extension(file) == '.py' and os.path.basename(file) != '__init__.py':
                name = os.path.basename(file).replace('.py', '')

                try:
                    Datafix.objects.get(name=name)
                except ObjectDoesNotExist:
                    Datafix.create_datafix(name)

    @staticmethod
    def create_datafix(name, module):
        workflow_datafix_dir = Datafix.get_workflow_datafix_path()
        datafix_dir = Datafix.get_module_datafix_path(module)

        file_name = datafix_dir + name + '.py'
        workflow_file_name = workflow_datafix_dir + name + '.py'

        if not os.path.exists(file_name) and not os.path.exists(workflow_file_name):
            raise Exception('Expected datafix file to exist at either: ' + file_name + ' or ' + workflow_file_name)

        timestamp = re.sub(r"(.*_)", "", name)

        datafix = Datafix(name=name, timestamp=timestamp)
        datafix.save()

        return datafix

    def run(self):
        _model_logger.info('running datafix: ' + self.name)

        workflow_datafix_dir =  Datafix.get_workflow_datafix_path()
        datafix_dir = Datafix.get_module_datafix_path(module)

        file_name = datafix_dir + self.name + '.py'
        workflow_file_name = workflow_datafix_dir + self.name + '.py'

        if os.path.exists(file_name):
            self.run_datafix(file_name)
        elif os.path.exists(workflow_file_name):
            self.run_datafix(workflow_file_name)
        else:
            raise Exception('Expected datafix file to exist at either: ' + file_name + ' or ' + workflow_file_name)

        self.run_at = timezone.now()
        self.save()

    def run_datafix(self, datafix_file):
        with open(datafix_file,"r") as code:
            exec(code.read())

    # TODO: deprecate - hardcoded development
    def create_file(self, use_workflow_engine, module):

        if use_workflow_engine:
            datafix_dir = Datafix.get_workflow_datafix_path()
        else:
            datafix_dir = Datafix.get_module_datafix_path(module)

        if not os.path.exists(datafix_dir):
            os.makedirs(datafix_dir)

        file_name = datafix_dir + self.name + '.py'

        with open(file_name, 'w') as datafix_file:
            datafix_file.write('#!/usr/bin/python\n')
            datafix_file.write('from django.db import transaction\n')
            datafix_file.write('from workflow_engine.models import *\n')
            datafix_file.write('from ' + module.__name__ + '.models import *\n\n')
            datafix_file.write('@transaction.atomic\n')
            datafix_file.write('def populate_database():\n')
            datafix_file.write('    #put your code here\n')
            datafix_file.write("    print('populating database...')\n")
            datafix_file.write('\n')
            datafix_file.write('populate_database()')
