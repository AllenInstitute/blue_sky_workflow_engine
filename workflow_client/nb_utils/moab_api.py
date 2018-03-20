import requests
from requests.auth import HTTPBasicAuth
import simplejson as json

#
# See: http://docs.adaptivecomputing.com/mws/7-1-1/guide/apiDocumentation.html#rest
#

_MOAB_ENDPOINT = 'http://qmaster2.corp.alleninstitute.org:8080/mws/rest'

def moab_url(
    table=None,
    oid=None,
    user=None):
    url_list = [ _MOAB_ENDPOINT ]
    
    if table is not None:
        url_list.append('/{}'.format(table))
    
    if oid is not None:
        url_list.append('/{}'.format(oid))
    
    param_list = []
                        
    if user is not None:
        param_list.append("""query={"credentials.user":"%s"}""" % (user))

    param_list.append('api-version=3')
    
    if len(param_list) > 0:
        url_list.append('?')
        url_list.append('&'.join(param_list))
    
    return ''.join(url_list)   

def moab_query(url, user, passwd):
    s = requests.get(
        url,
        auth=HTTPBasicAuth(user, passwd)).content

    return json.loads(s)['results']

