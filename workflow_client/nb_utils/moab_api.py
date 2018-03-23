import requests
from requests.auth import HTTPBasicAuth
import simplejson as json
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
    jobs=None):
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
    
    result_data = json.loads(s)['results']

    return result_data

