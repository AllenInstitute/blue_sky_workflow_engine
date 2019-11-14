# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2019. Allen Institute. All rights reserved.
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
from workflow_engine.mixins import Archivable, Timestamped
import logging


class WorkflowEdge(Archivable, Timestamped, models.Model):
    '''Links workflow nodes together to define :ref:`workflows`.
    Provides a through table for many-to-many relation between workflow nodes.
    '''

    _log = logging.getLogger('workflow_engine.models.workflow_edge')

    workflow = models.ForeignKey(
        'workflow_engine.Workflow',
        on_delete=models.CASCADE
    )
    '''The workflow graph containing this edge and related nodes'''

    source = models.ForeignKey(
        'workflow_engine.WorkflowNode',
        related_name='%(class)s_source',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    '''Association to the workflow node leading into the edge (or null)'''

    sink = models.ForeignKey(
        'workflow_engine.WorkflowNode',
        related_name='%(class)s_sink',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    '''Association to the workflow node leading out of the edge (or null)'''

    disabled = models.BooleanField(default=False)
    '''Mark an edge that is not to be used temporarily.'''

    priority = models.PositiveIntegerField(
        default=1
    )
    '''Used for sort order'''

    class Meta:
        ordering = ('priority',)


    def __str__(self):
        '''Human readable name in terms of the source and sink nodes'''
        return "{} -> {}".format(str(self.source), str(self.sink))
