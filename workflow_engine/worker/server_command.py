import os
import paramiko
import logging
import codecs
_log = logging.getLogger('workflow_engine.worker.server_command')

def check_environment_variables():
    if "QMASTER_USERNAME" not in os.environ:
        raise Exception('Please set QMASTER_USERNAME environment variable')

    if "QMASTER_PASSWORD" not in os.environ:
        raise Exception('Please set QMASTER_PASSWORD environment variable')

def server_command(host, port,
                   username,
                   crd,
                   command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    enc = codecs.getencoder('rot-13')
    with open(crd) as f:
        pswd = enc(f.readline().strip())[0]

    _log.info('qmaster cred: %s %s %s %d' % (
        host, username, '*', port))

    client.connect(host,
                   username=username,
                   password=pswd,
                   port=port)
    stdin, stdout, stderr = client.exec_command(command)
    stdout_message = stdout.readlines()
    stderr_message = stderr.readlines()

    return stdout_message, stderr_message
