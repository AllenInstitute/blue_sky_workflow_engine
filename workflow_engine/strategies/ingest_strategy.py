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
from workflow_engine.strategies.execution_strategy \
    import ExecutionStrategy
from workflow_engine.import_class import import_class
import traceback
import logging

class IngestStrategy(ExecutionStrategy):
    _log = logging.getLogger('workflow_engine.strategies.ingest_strategy')
    #####everthing bellow this can be overriden#####

    def get_workflow_name(self):
        '''used to query the workflow object for start_workflow

        Returns
        -------
        String
            machine readable workflow name
        '''
        return None

    def create_enqueued_object(self, dictionary, tags=None):
        return None

    def generate_response(self, enqueued_object):
        return None

    #override if needed

    #####everthing bellow this should not be overriden#####
    #Do not override
    def skip_execution(self, enqueued_object):
        '''override executing jobs, only create enqueued objects

        Ingest strategies are derived from executable strategies,
        but are not used to execute jobs.

        Returns
        -------
        boolean
            always true
        '''
        return True

    def is_ingest_strategy(self):
        return True

    def is_execution_strategy(self):
        return False

    @classmethod
    def call_ingest_strategy(cls, wf_name, message):
        wf = Workflow.objects.get(name=wf_name)
        IngestStrategy._log.info('ingest ' + str(wf) + ' ' + str(message))

        ingest_strategy_class_name = wf.ingest_strategy_class
        IngestStrategy._log.info(
            'workflow strategy class: %s' % (ingest_strategy_class_name))

        clz = import_class(ingest_strategy_class_name)
        ingest_strategy = clz()

        return ingest_strategy.ingest_message(message)


    def ingest_message(self, workflow_name, message, tags=None):
        if tags == None:
            tags = []

        enqueued_object, start_node = \
            self.create_enqueued_object(
                message, tags)

        ret = self.generate_response(enqueued_object)

        IngestStrategy._log.info("Starting workflow: %s", workflow_name)

        WorkflowController.start_workflow(
            workflow_name,
            enqueued_object,
            start_node_name=start_node)

        return ret


from workflow_engine.workflow_controller import WorkflowController
from workflow_engine.models import Workflow
