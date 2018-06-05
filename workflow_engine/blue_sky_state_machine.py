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
from django.core.exceptions import FieldDoesNotExist
import logging

class FailedExecutionException(Exception):
    pass

class IllegalStateTransition(FailedExecutionException):
    def __init__(self, model, field, from_state, to_state):
        self.model = model,
        self.field = field,
        self.from_state = from_state
        self.to_state = to_state


class BlueSkyStateMachine:
    _log = logging.getLogger('workflow_engine.blue_sky_state_machine')


    def __init__(self, machines):
        if machines is None:
            self.machines = {}
        else:
            self.machines = machines

    def add_transition(self, state, transitions):
        self.transitions[state] = transitions

    def machine_key(self, model):
        return model._meta.label_lower.split('.')[-1]

    def states(self, model):
        return self.machines[self.machine_key(model)]['states']

    def transitions(self, model):
        return self.machines[self.machine_key(model)]['transitions']

    def in_state(self, model, state_machine_field, state_list):
        try:
            model._meta.get_field(state_machine_field)
            current_state = getattr(model, state_machine_field)

            BlueSkyStateMachine._log.info(
                "%s in %s", str(current_state), str(state_list))

            if current_state in state_list:
                return True

            return False
        except FieldDoesNotExist:
            mess = 'Field named: ' + str(state_machine_field) + ' does not exist'
            BlueSkyStateMachine._log.error(mess)
            raise Exception(mess)

    def can_transition(self, model, from_state, to_state):
        transitions = self.transitions(model)
        allowed = transitions.get(from_state, [])

        return to_state in allowed

    def transition(self, model, state_machine_field, to_state, force=False):
        try:
            model._meta.get_field(state_machine_field)

            current_state = getattr(model, state_machine_field)

            if force or self.can_transition(model, current_state, to_state):
                setattr(model, state_machine_field, to_state)
                model.save()
            else:
                mess = 'State: ' + str(current_state) + ' cannot transition to ' + str(to_state)
                BlueSkyStateMachine._log.error(mess)
                raise IllegalStateTransition(
                    model, state_machine_field, current_state, to_state)

        except FieldDoesNotExist:
            mess = 'Field named: ' + str(state_machine_field) + ' does not exist'
            BlueSkyStateMachine._log.error(mess)
            raise Exception(mess)
