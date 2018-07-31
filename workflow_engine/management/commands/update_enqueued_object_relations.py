# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2018. Allen Institute. All rights reserved.
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
from django.core.exceptions import ObjectDoesNotExist
from workflow_engine.models.job import Job
from workflow_engine.models.task import Task
from workflow_engine.models.workflow_node import WorkflowNode
from django.contrib.contenttypes.models import ContentType
from workflow_engine.import_class import import_class
import logging


class Command(BaseCommand):
    _log = logging.getLogger(
    'workflow_engine.mananagement.commands.update_enqueued_object_relations')
    help = 'Import Workflow Definitions from YAML'

    def add_arguments(self, parser):
        parser.add_argument('dry_run')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        print(dry_run)

        try:
            wns = WorkflowNode.objects.all()
            for wn in wns:
                print(str(wn))
                eoc_string = wn.job_queue.enqueued_object_class
                eoc = import_class(eoc_string)
                eo_content_type = ContentType.objects.get_for_model(eoc)

                if dry_run == 'false':
                    wn.job_queue.enqueued_object_type = eo_content_type
                    wn.job_queue.save()

                js = Job.objects.filter(workflow_node=wn)

                for j in js:
                    print("{} / {} / {}".format(
                        str(j),
                        str(eoc_string),
                        eo_content_type))
                    if dry_run == 'false':
                        j.enqueued_object_type = eo_content_type
                        j.save()

                ts = Task.objects.filter(job__workflow_node=wn)
                for t in ts:
                    eto_string = t.enqueued_task_object_class
                    eto = import_class(eto_string)
                    eto_content_type = ContentType.objects.get_for_model(eto)
                    print("{} / {} / {}".format(
                        str(t),
                        str(eto_string),
                        eto_content_type))
                    if dry_run == 'false':
                        t.enqueued_task_object_type = eto_content_type
                        t.save()
        except Exception as e:
            Command._log.error('Something went wrong: ' + str(e))
            raise(e)
