# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2021. Allen Institute. All rights reserved.
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
from django.conf import settings
from urllib3 import PoolManager
import pandas as pd
import json
from json import JSONDecodeError
import os
import logging
#
# See: http://docs.adaptivecomputing.com/mws/7-1-1/guide/apiDocumentation.html#rest
#
_log = logging.getLogger(
    'workflow_engine.process.workers.slurm_api'
)

class SlurmApi(object):
    def __init__(self):
        self.http = PoolManager()

    def slurm_url(self, table=None, oid=None):
        url_list = [ settings.SLURM_ENDPOINT ]

        if table is not None:
            url_list.append(f'/{table}')
    
        if oid is not None:
            url_list.append(f'/{oid}')
    
        query_url = ''.join(url_list)

        _log.info(query_url)

        return query_url

    def slurm_cred(self):
        cred = settings.SLURM_AUTH

        if cred == ':':
            raise Exception('credentials not set')

        try:
            (user, token) = cred.split(':', 1)
        except ValueError:
            _log.error('check SLURM_AUTH format')

        return (user, token)

    def slurm_headers(self):
        user, token = self.slurm_cred()

        headers = {
            "Content-Type": "application/json",
            "X-SLURM-USER-NAME": user,
            "X-SLURM-USER-TOKEN": token
        }

        return headers

    def slurm_post(self, url, body_data):
        return self.slurm_send(url, body_data, mode='POST')

    def slurm_query(self, url):
        return self.slurm_send(url, body_data=None, mode='GET')

    def slurm_send(self, url, body_data, mode='GET'):
        response = self.http.request(
            mode,
            url,
            headers=self.slurm_headers(),
            body=body_data)

        try:
            status = response.status
            if status == 401:
                _log.warning('SLURM credential failure {}'.format(url))
            response_data = json.loads(response.data)
        except Exception as e:
            _log.error('SLURM error' + str(e) + ', ' + ', ' + str(url))
            response_data = 'Error'

        return response_data
    
    def submit_job_payload(
        self,
        task_id,
        command_dir,
        command_script,
        duration_seconds=600,
        processors=1,
        tasks=1,
        slurm_cfg=None):
    
        url = self.slurm_url(table='job', oid='submit')

        user,_ = self.slurm_cred()
    
        payload = {
            "job": {
                "account": user,
                "ntasks": 1,
                "cpus_per_task": processors,
                "name": f"task_{task_id}",
                "current_working_directory": command_dir,
                "time_limit": duration_seconds,
                "environment": {
                    "PATH": "/bin:/usr/bin:/usr/local/bin"
                }
            },
            "script": command_script
        }
    
        return payload
    
    
    def submit_job(
        self,
        task_id,
        command_dir,
        command_script,
        duration_seconds=600,
        processors=1,
        tasks=1,
        slurm_cfg=None
    ):
        """
           See: https://slurm.schedmd.com/rest_api.html#slurmctldSubmitJob
        """
        url = self.slurm_url(
            table='job',
            oid='submit')

        payload = self.submit_job_payload(
            task_id,
            command_dir,
            command_script,
            duration_seconds,
            processors,
            tasks,
            slurm_cfg)
        try:
            response_message = self.slurm_post(
                url,
                body_data=json.dumps(payload).encode('utf-8')
            )

            _log.info(response_message)
    
            if 'job_id' in response_message:
                slurm_id = response_message['job_id']
                _log.info('SLURM ID: %s', slurm_id)
            else:
                _log.info('SLURM response' + json.dumps(response_message))
                slurm_id = 'ERROR'
        except Exception as e:
            _log.error(e)
            raise e
            slurm_id = 'ERROR'
    
        return slurm_id
    
    def delete_slurm_task(self, slurm_id):
        url = self.slurm_url(
            table='job',
            oid=slurm_id)
        response = self.http.request(
            'DELETE',
            url,
            headers=self.slurm_headers()
        )

        if response.status == 200:
            return True
        else:
            return False
