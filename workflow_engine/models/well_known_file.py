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
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import os
import logging
_model_logger = logging.getLogger('workflow_engine.models')


class WellKnownFile(models.Model):
    attachable_id = models.PositiveIntegerField()
    attachable_type = models.ForeignKey(ContentType)
    well_known_file_type = models.CharField(max_length=255)
    content_object = GenericForeignKey('attachable_type', 'attachable_id')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def set(full_path, attachable_object, well_known_file_type, task=None):
        #make sure file is valid
        WellKnownFile.verify_file_exists(full_path)

        well_known_file = WellKnownFile.get_or_create_well_known_file(attachable_object, well_known_file_type)
        well_known_file.create_file_record_if_needed(full_path, task)

    #staticmethod
    def get(attachable_object, well_known_file_type):
        result = None

        try:
            well_known_file = WellKnownFile.objects.get(attachable_id=attachable_object.id, well_known_file_type=well_known_file_type)
            file_record = well_known_file.get_most_recent_file_record()
            result = file_record.get_full_name()
        except:
            result = None
    
        return result

    def get_next_order(self):
        order = ZERO

        for file_record in self.get_file_records():
            if file_record.order >= order:
                order = file_record.order + ONE

        return order

    @staticmethod
    def verify_file_exists(full_path):
        if not os.path.exists(full_path):
            raise Exception('Expected file to exist at: ' + str(full_path) + ' but it does not')

    @staticmethod
    def get_or_create_well_known_file(attachable_object, well_known_file_type):
        try:
            well_known_file = WellKnownFile.objects.get(attachable_id=attachable_object.id, well_known_file_type=well_known_file_type)
        except:
            well_known_file = WellKnownFile(content_object=attachable_object, well_known_file_type=well_known_file_type)
            well_known_file.save()

        return well_known_file

    def create_file_record_if_needed(self, full_path, task):
        filename = os.path.basename(full_path)
        storage_directory = os.path.dirname(full_path)

        most_recent_file = self.get_most_recent_file_record()

        if not most_recent_file or most_recent_file.filename != filename or most_recent_file.storage_directory != storage_directory:
            file_record = FileRecord(filename=filename, storage_directory=storage_directory, order=self.get_next_order(), well_known_file=self, task=task)
            file_record.save()
        else:
            most_recent_file.task = task
            most_recent_file.save()

    def get_file_records(self):
        return FileRecord.objects.filter(well_known_file_id=self.id).order_by('order')

    def get_most_recent_file_record(self):
        try:
            file_records = self.get_file_records()
            last_element = len(file_records) - ONE
            result = file_records[last_element]
        except:
            result = None

        return result
