# Allen Institute Software License - This software license is the 2-clause BSD
# license plus a third clause that prohibits redistribution for commercial
# purposes without further permission.
#
# Copyright 2018-2019. Allen Institute. All rights reserved.
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
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import json
from json import JSONDecodeError
import os
import logging
#
# See: http://docs.adaptivecomputing.com/mws/7-1-1/guide/apiDocumentation.html#rest
#
_log = logging.getLogger(
    'workflow_engine.process.workers.moab.moab_api'
)


def moab_url(
    table=None,
    oid=None,
    user=None,
    jobs=None,
    tasks=None,
    moab_ids=None):
    url_list = [ settings.MOAB_ENDPOINT ]
    
    if table is not None:
        url_list.append('/{}'.format(table))
    
    if oid is not None:
        url_list.append('/{}'.format(oid))
    
    param_list = []

    if user is not None:
        param_list.append(
            "query=" + 
            requests.compat.quote_plus(
                """{"credentials.user":"%s"}""" % (user)))

    if jobs is not None:
        job_list = ','.join('"%d"' % (jid) for jid in jobs)
        param_list.append(
            "query=" + 
            requests.compat.quote_plus(
                '{"name": { $in: [%s]} }' % (job_list)))

    if tasks is not None:
        task_list = ','.join(
            '"task_%d"' % (tid) for tid in tasks)
        param_list.append(
            "query=" + 
            requests.compat.quote_plus(
                '{"customName": { $in: [%s]} }' % (task_list)))

    if moab_ids is not None:
        _log.info('MOAB IDS: %s', str(moab_ids))
        moab_ids = [m for m in moab_ids if m is not None]
        moab_list = '"' + '","'.join(moab_ids) + '"'
        param_list.append(
            "query=" + 
            requests.compat.quote_plus(
                '{"name": { $in: [%s]} }' % (moab_list)))

    param_list.append('api-version=3')
    
    if len(param_list) > 0:
        url_list.append('?')
        url_list.append('&'.join(param_list))

    query_url = ''.join(url_list)

    _log.info(query_url)

    return query_url


def moab_auth():
    cred = settings.MOAB_AUTH

    if cred == ':':
        raise Exception('credentials not set')

    try:
        (moab_user, moab_pass) = cred.split(':', 1)
    except ValueError:
        _log.error('check MOAB_AUTH format')

    auth = HTTPBasicAuth(moab_user, moab_pass)
    _log.info('AUTH: {}'.format(auth))

    return auth


def moab_query(url):
    try:
        response= requests.get(
            url,
            auth=moab_auth())

        if response.status_code == 200:
            result_data = response.json()

            if 'results' in result_data:
                result_data = result_data['results']
        elif response.status_code == 401:
            _log.error('Bad moab credentials')
            result_data = "Error"
        else:
            _log.error('Moab response code: {}'.format(response.status_code))

            result_data = "Error"

        return result_data

    except JSONDecodeError as e:
        _log.error('Moab JSON decode error')
    except Exception as e:
        _log.error('Moab query ' + str(e) + ', ' + ', ' + str(url))
        raise e


def moab_post(url, body_data):
    try:
        response = requests.post(
            url,
            json=body_data,
            auth=moab_auth(),
            timeout=settings.MOAB_TIMEOUT
        )

        if response.status_code == 401:
            _log.warning('MOAB credential failure {}'.format(url))

        _log.info('RESPONSE STATUS: ' + str(response.status_code))

        s = response.text

        _log.info('RESPONSE TEXT: ' + str(response))
    except requests.exceptions.Timeout as e:
        _log.error('Moab post timeout ' + str(e) + ', ' + ', ' + str(url) + '\n' + json.dumps(body_data, indent=2))
        raise e
    except Exception as e:
        _log.error('Moab post 1 ' + str(e) + ', ' + ', ' + str(url))
        raise e

    _log.info('MOAB POST: ' + str(s))

    try:
        result_data = json.loads(s)
    except Exception as e:
        _log.error('Moab post 2 ' + str(e) + ', ' + ', ' + str(s))
        raise e

    return result_data



def moab_delete(url):
    s = requests.delete(
        url,
        auth=moab_auth()
    ).content

    result_data = json.loads(s)

    return result_data


def workflow_state_dataframe(state_dict):
    """
    state_dict: { id: "<state>" }
    """
    workflow_state_df = pd.DataFrame(
        state_dict,
        columns=['task_id', 'workflow_state', 'moab_id'])

    _log.info('workflow_state_df: ' + str(workflow_state_df))

    workflow_state_df['task_name'] = \
        workflow_state_df['task_id'].map(
            lambda s: 'task_%d' % (s))

    return workflow_state_df


def query_moab_state(state_dicts):
    """
    state_dicts: [{ 'moab_id': 'Moab.123'}, ... ]
    """
    moab_dict = moab_query(
        moab_url(
            table='jobs',
            moab_ids=[d['moab_id'] for d in state_dicts]))

    _log.info('moab dict: {}'.format(
        json.dumps(moab_dict, indent=2)))

    column_names = [
        'moab_id', 'task_name', 'moab_state', 'active', 'user', 'exit_code'
    ]

    try:
        moab_state_df = pd.DataFrame.from_records([
            (job['name'],
             job['customName'],
             job['states']['state'],
             job['isActive'],
             job['credentials']['user'],
             job['completionCode']) for job in moab_dict],
            columns=column_names
        )

        active_idx = moab_state_df.loc[moab_state_df.active == True].index
        moab_state_df.loc[active_idx,['moab_state']] = 'Running'
    except:
        moab_state_df = pd.DataFrame(columns=column_names)

    return moab_state_df


def combine_workflow_moab_states(workflow_dataframe,
                                 moab_dataframe):

    try:
        combined_df = pd.DataFrame.merge(
            workflow_dataframe,
            moab_dataframe,
            on=["task_name", 'moab_id'],
            how="outer")
    
        # work around pandas issues w/ NaN in int columns
        # and merge promotion
        combined_df.task_id.fillna(0, inplace=True)
        combined_df.task_id = combined_df.task_id.astype(int)
    
        combined_df['moab_state'] = \
            combined_df['moab_state'].fillna('Unknown')
    
        combined_df['running_message'] = False
        combined_df['finished_message'] = False
        combined_df['failed_message'] = False
        combined_df['failed_execution_message'] = False
    
        combined_df.loc[
            combined_df.workflow_state.isin(["QUEUED"]) &
            combined_df.moab_state.isin(["Running"]),
            'running_message'] = True
    
        combined_df.loc[
            combined_df.workflow_state.isin(["QUEUED","RUNNING"]) &
            combined_df.moab_state.isin(["Completed"]) &
            (combined_df.exit_code == 0),
            'finished_message'] = True
    
        combined_df.loc[
            combined_df.workflow_state.isin(["QUEUED","RUNNING"]) &
            combined_df.moab_state.isin(["Completed"]) &
            (combined_df.exit_code != 0),
            'failed_message'] = True
    
        combined_df.loc[
            combined_df.workflow_state.isin(["QUEUED","RUNNING"]) &
            combined_df.moab_state.isin(
                ["Expired", "Removed", "Vacated", "Unknown"]),
            'failed_execution_message'] = True
    except:
        return pd.DataFrame()

    return combined_df


def query_and_combine_states(state_dict):
    """
    state_dict: { id: "<state>" }
    """
    workflow_state_df = workflow_state_dataframe(state_dict)
    moab_state_df = query_moab_state(state_dict)

    _log.info('moab state df: {}'.format(str(moab_state_df)))

    combined_df = combine_workflow_moab_states(
        workflow_state_df, moab_state_df)

    return combined_df


def submit_job(
    task_id,
    command_file,
    duration_seconds=600,
    processors=1,
    tasks=1,
    user='',
    moab_cfg=None):
    url = moab_url(table='jobs')

    payload = {
        'customName': 'task_%d' % (task_id),
        'commandFile': command_file,
        'epilog': os.path.join(os.path.dirname(command_file), 'epilog'),
        'group': settings.MOAB_GROUP,
        'user': user,
        'requirements': [{
            'requiredProcessorCountMinimum': processors,
            'tasksPerNode': tasks,
            'taskCount': 1,
        }],
        'durationRequested': duration_seconds
    }

    if moab_cfg:
        if 'excluded_nodes' in moab_cfg:
            payload['nodesExcluded'] = [
                { 'name': n } for n in moab_cfg['excluded_nodes']
            ]

    _log.info('PAYLOAD: {}'.format(json.dumps(payload, indent=2)))

    try:
        response_message = moab_post(
            url,
            body_data=payload)

        if 'name' in response_message:
            moab_id = response_message['name']
            _log.info('MOAB ID: %s', moab_id)
        else:
            _log.info('MOAB response' + json.dumps(response_message))
            moab_id = 'ERROR'
    except Exception as e:
        _log.error(e)
        raise e
        moab_id = 'ERROR'

    return moab_id


def submit_job_array(
    task_id,
    command_file,
    duration_seconds=240,
    processors=1,
    tasks=1,
    user='',
    moab_cfg=None):
    url = moab_url(table='job-arrays')

    ppn = 32
    n_nodes = 3
    total_processors = ppn * n_nodes

    try:
        payload = {
            'name': 'task_{}'.format(task_id),
            'indexValues': list(range(0, n_nodes)),
            'jobPrototype' : {
                'customName': 'task_{}'.format(task_id),
                'commandFile': command_file,
                'group': 'em-connectome',
                'user': user,
                'requirements': [{
                    'requiredProcessorCountMinimum': total_processors,
                    'tasksPerNode': 1,
                    'taskCount': n_nodes
#                    'resourcesPerTask': {
#                        'processors': { 'dedicated': ppn }
 #                   }
                }],
                'durationRequested': duration_seconds
            }
        }

        if moab_cfg and 'excluded_nodes' in moab_cfg:
            payload['jobPrototype']['nodesExcluded'] = [
                { 'name': n } for n in moab_cfg['excluded_nodes']
            ]
    except Exception as e:
        _log.error(e)
        moab_id = 'ERROR'
        return moab_id

    _log.info('payload: ' + str(json.dumps(payload, indent=2)))

    try:
        response_message = moab_post(
            url,
            body_data=payload)
    except Exception as e:
        _log.error(str(e))
        moab_id = 'ERROR'
        return moab_id

    try:
        if 'name' in response_message:
            moab_id = response_message['name']
            _log.info('MOAB ID: %s', moab_id)
        else:
            _log.info('MOAB response' + json.dumps(response_message))
            moab_id = 'ERROR'
    except Exception as e:
        _log.error(e)
        moab_id = 'ERROR'

    return moab_id


def delete_moab_task(moab_id):
    url = moab_url(
        table='jobs',
        oid=moab_id)

    return moab_delete(url)
