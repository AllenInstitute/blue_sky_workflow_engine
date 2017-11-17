import os
import paramiko
import logging
_log = logging.getLogger('workflow_client.server_command')

def check_environment_variables():
    if "QMASTER_USERNAME" not in os.environ:
        raise Exception('Please set QMASTER_USERNAME environment variable')

    if "QMASTER_PASSWORD" not in os.environ:
        raise Exception('Please set QMASTER_PASSWORD environment variable')

def server_command(host, port,
                   username, password,
                   command):
    check_environment_variables()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    _log.info('qmaster cred: %s %s %s %d' % (
        host, username, '*', port))
       
    client.connect(host,
                   username=username,
                   password=password,
                   port=port)
    stdin, stdout, stderr = client.exec_command(command)
    stdout_message = stdout.readlines()
    stderr_message = stderr.readlines()

    return stdout_message, stderr_message

if __name__ == '__main__':
    host = os.environ.get('QMASTER_HOST', 'qmaster')
    username = os.environ['QMASTER_USERNAME']
    password = os.environ['QMASTER_PASSWORD']
    port = int(os.environ.get('QMASTER_PORT', '22'))

    command = 'echo hi'

    server_command(host, port, username, password, command)
