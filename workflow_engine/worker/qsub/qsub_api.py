from workflow_client.nb_utils.moab_api \
    import combine_workflow_moab_states, \
    workflow_state_dataframe
from workflow_engine.worker.server_command import server_command
import pandas as pd
import logging
import re
#
# See: http://docs.adaptivecomputing.com/mws/7-1-1/guide/apiDocumentation.html#rest
#
_log = logging.getLogger('workflow_engine.worker.qsub.qsub_api')


# _MOAB_ENDPOINT = 'http://qmaster2.corp.alleninstitute.org:8080/mws/rest'


def parse_qstat_full_output(lines):
    qstat_dicts = []
    qstat_dict = None

    state_mapping = {
        'Q': 'Queued',
        'R': 'Running',
        'C': 'Complete'
    }

    for i in range(0, len(lines)):
        m = re.match(r'^Job Id:\s+(\d+)\.', lines[i])
        if m:
            if qstat_dict is not None:
                qstat_dicts.append(qstat_dict)
            qstat_dict = {
                'id': m.group(1),
                'completionCode': None
            }
        else:
            m = re.match(r"^\s+(\S+)\s=\s(\S+).*$", lines[i])
            if m:
                key = m.group(1)
                value = m.group(2)
                if key == 'Job_Name':
                    qstat_dict['customName'] = value
                    qstat_dict['name'] = int(value.replace(
                        'task_', ''))
                elif key == 'Job_Owner':
                    qstat_dict['credentials'] = { 
                        'user': value }
                elif key == 'job_state':
                    qstat_dict['states'] = { 
                        'state': state_mapping.get(
                            value, 'Unknown') }
                elif key == 'exit_status':
                    qstat_dict['exit_code'] = value
                else:
                    pass

    qstat_dicts.append(qstat_dict)

    return qstat_dicts


def qstat_query():
    return parse_qstat_full_output(
        server_command(
            'hpc-login.corp.alleninstitute.org',
            22,
            'svc_vol_assem',
            '/local1/git/at_em_imaging_workflow/at_em_imaging_workflow/hpc.crd',
            'qstat -f -u svc_vol_assem')[0])


def query_qstat_moab_state(state_dicts):
    """
    state_dicts: [{ 'moab_id': 'Moab.123'}, ... ]
    """
    moab_dict = qstat_query()

    moab_state_df = pd.DataFrame.from_records([
        (job['name'],
         job['customName'],
         job['states']['state'],
         job['credentials']['user'],
         job['completionCode']) for job in moab_dict],
        columns=[
            'moab_id', 'task_name', 'moab_state', 'user', 'exit_code']
    )

    return moab_state_df


def query_and_combine_qstat_states(state_dict):
    """
    state_dict: { id: "<state>" }
    """
    workflow_state_df = workflow_state_dataframe(state_dict)
    moab_state_df = query_qstat_moab_state(state_dict)
     
    combined_df = combine_workflow_moab_states(
        workflow_state_df, moab_state_df)
 
    return combined_df


# def submit_job(
#     task_id,
#     command_file,
#     duration_seconds=600,
#     processors=1,
#     tasks=1,
#     user='timf'):
#     url = moab_url(table='jobs')
# 
#     try:
#         payload = {
#             'customName': 'task_%d' % (task_id),
#             'commandFile': command_file,
#             'group': 'em-connectome',
#             'user': user,
#             'requirements': [{
#                 'requiredProcessorCountMinimum': processors,
#                 'tasksPerNode': tasks,
#                 'taskCount': 1,
#             }],
#             'durationRequested': duration_seconds
#         }
#     
#         _log.info('MOAB URL: %s', url)
#         _log.info('MOAB task_id: %d', task_id)
#         _log.info('MOAB commandFile: %s', command_file)
#         _log.info('MOAB user: %s', user)
#         _log.info('MOAB processors: %d', processors)
#         _log.info('MOAB tasks: %d', tasks)
#         _log.info('MOAB duration_seconds: %d', duration_seconds)
# 
#         _log.info('body_data: ' + json.dumps(payload))
#     
#         response_message = moab_post(
#             url,
#             body_data=payload)
# 
#         if 'name' in response_message:
#             moab_id = response_message['name']
#             _log.info('MOAB ID: %s', moab_id)
#         else:
#             _log.info('MOAB response' + json.dumps(response_message))
#             moab_id = 'ERROR'
#     except Exception as e:
#         _log.error(e)
#         moab_id = 'ERROR'
# 
#     return moab_id


# def delete_moab_task(moab_id):
#     url = moab_url(
#         table='jobs',
#         oid=moab_id)
# 
#     return moab_delete(url)
