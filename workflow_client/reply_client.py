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
import pika
import simplejson as json
import logging


class ReplyClient(object):
    _log = logging.getLogger('workflow_client.reply_client')

    def __init__(self,
                 host, port,
                 user, password,
                 exchange, route_key):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host, port, '/',
                pika.PlainCredentials(user, password)))
        self.exchange = exchange
        self.route_key = route_key

    def __enter__(self):
        self.channel = self.connection.channel()
        return self

    def __exit__(self, type, value, traceback):
        self.connection.close()

    def send_json(self, json_string):
        self.channel.basic_publish(exchange=self.exchange,
                                   routing_key=self.route_key,
                                   body=json_string)
        ReplyClient._log.info("Sent '%s'" % (json_string))

    def send_as_json(self, data_dict):
        self.send_json(json.dumps(data_dict))

    def send(self, body_data):
        self.channel.basic_publish(exchange=self.exchange,
                                   routing_key=self.route_key,
                                   body=body_data)
        ReplyClient._log.info("Sent '%s'" % (body_data))
