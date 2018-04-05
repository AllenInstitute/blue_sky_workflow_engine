import requests
from requests.auth import HTTPBasicAuth
import simplejson as json
import pandas as pd
import os
import logging
#
# See: http://docs.adaptivecomputing.com/mws/7-1-1/guide/apiDocumentation.html#rest
#
_log = logging.getLogger('workflow_client.nb_utils.moab_api')


_MOAB_ENDPOINT = 'http://qmaster2.corp.alleninstitute.org:8080/mws/rest'


def moab_url(
    table=None,
    oid=None,
    user=None,
    jobs=None,
    tasks=None):
    url_list = [ _MOAB_ENDPOINT ]
    
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

    param_list.append('api-version=3')
    
    if len(param_list) > 0:
        url_list.append('?')
        url_list.append('&'.join(param_list))

    query_url = ''.join(url_list)

    _log.info(query_url)

    return query_url


def moab_auth():
    (moab_user, moab_pass) = \
        os.environ.get('MOAB_AUTH', 'user:pass').split(':', 1)

    return HTTPBasicAuth(moab_user, moab_pass)


def moab_query(url):
    s = requests.get(
        url,
    auth=moab_auth()).content

    result_data = json.loads(s)

    if 'results' in result_data:
        result_data = result_data['results']

    return result_data


def moab_post(url, body_data):
    s = requests.post(
        url,
        json=body_data,
        auth=moab_auth()
    ).text   # todo: content?

    #result_data = json.loads(s)

    #return result_data
    return s


def workflow_state_dataframe(state_dict):
    """
    state_dict: { id: "<state>" }
    """
    workflow_state_df = pd.DataFrame.from_records(
        list(state_dict.items()),
        columns=['task_id', 'workflow_state'])
    
    workflow_state_df['task_name'] = \
        workflow_state_df['task_id'].map(
            lambda s: 'task_%d' % (s))

    return workflow_state_df


def query_moab_state(state_dict):
    """
    state_dict: { id: "<state>" }
    """
    moab_dict = moab_query(
        moab_url(
            table='jobs',
            tasks=state_dict.keys()))

    moab_state_df = pd.DataFrame.from_records([
        (job['name'],
         job['customName'],
         job['states']['state'],
         job['credentials']['user']) for job in moab_dict],
        columns=['name', 'task_name', 'moab_state', 'user']
    )

    return moab_state_df


def combine_workflow_moab_states(workflow_dataframe,
                                 moab_dataframe):
    combined_df = pd.DataFrame.merge(
        workflow_dataframe,
        moab_dataframe,
        on="task_name",
        how="outer")

    # work around pandas issues w/ NaN in int columns
    # and merge promotion
    combined_df.task_id.fillna(0, inplace=True)
    combined_df.task_id = combined_df.task_id.astype(int)

    combined_df['moab_state'] = \
        combined_df['moab_state'].fillna('Expired')

    combined_df['running_message'] = False
    combined_df['finished_message'] = False
    combined_df['failed_message'] = False

    combined_df.loc[
        combined_df.workflow_state.isin(["QUEUED"]) &
        combined_df.moab_state.isin(["Running"]),
        'running_message'] = True

    combined_df.loc[
        combined_df.workflow_state.isin(["QUEUED","RUNNING"]) &
        combined_df.moab_state.isin(["Completed"]),
        'finished_message'] = True

    combined_df.loc[
        combined_df.workflow_state.isin(["QUEUED","RUNNING"]) &
        combined_df.moab_state.isin(["Expired"]),
        'failed_message'] = True

    return combined_df


def query_and_combine_states(state_dict):
    """
    state_dict: { id: "<state>" }
    """
    workflow_state_df = workflow_state_dataframe(state_dict)
    moab_state_df = query_moab_state(state_dict)
    
    combined_df = combine_workflow_moab_states(
        workflow_state_df, moab_state_df)

    return combined_df


def submit_job(
    task_id,
    command_file,
    duration_seconds=600,
    processors=1,
    tasks=1,
    user='timf'):
    url = moab_url(table='jobs')

    payload = {
        'customName': 'task_%d' % (task_id),
        'commandFile': command_file,
        'group': 'em-connectome',
        'user': user,
        # 'initialWorkingDirectory': '/home/timf',
        'requirements': [{
            'requiredProcessorCountMinimum': processors,
            'tasksPerNode': tasks,
            'taskCount': 1,
        }],
        'durationRequested': duration_seconds
    }

    return moab_post(
        url,
        body_data=payload)
