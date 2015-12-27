__author__ = 'Vladislav'
import threading
import paramiko
import yaml
from subprocess import Popen, PIPE
from time import sleep
import sys

DOCKER = 'docker'
VAGRANT = 'vagrant'


def manage_script(args, print_output=False, print_errors=False):
    sleep(2)
    child = Popen(args, stdout=PIPE, stderr=PIPE)

    output = child.stdout.read()
    err = child.stderr.read()
    if print_output:
        print output
    if print_errors:
        print err

    child.communicate()
    rc = child.returncode
    return rc


def load_key(path):
    return paramiko.RSAKey.from_private_key_file(path)


def get_containers_data():
    with open("/etc/pgluster/config.yml", 'r') as stream:
        return yaml.load(stream)


def server_run_cmd(host, user, key, cmd):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(
        paramiko.AutoAddPolicy()
    )

    rsa_key = key
    ssh.connect(host, username=user, pkey=rsa_key, banner_timeout=120, timeout=120)
    if type(cmd) is list:
        for cmd_run in cmd:
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd_run)
    else:
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)

    rc = ssh_stdout.channel.recv_exit_status()
    ssh.close()
    return rc


def link_servers(nodes, name, vol, brick, key):
    response = ''
    status = False

    peer_command = ''
    start_command = 'gluster volume start ' + vol
    connect_command = 'gluster volume create ' \
                      + vol \
                      + ' transport tcp '

    for node in nodes:
        if node['status'] == 1:
            peer_command += "gluster peer probe " + node['ip'] + "; "
            connect_command += " " + node['ip'] + ":" + brick
            first_node = node

    connect_command += " force"

    peer_command = 'docker exec ' + name + " /bin/sh -c '" + peer_command + "'"
    rc = server_run_cmd(first_node['ip'], first_node['user'], key, peer_command)

    if rc > 0:

        response += "server peer connecting fail\n"
        return status, response
    else:
        response += "server peer connecting good\n"

    connect_command = 'docker exec ' + name + " /bin/sh -c '" + connect_command + "'"
    rc = server_run_cmd(first_node['ip'], first_node['user'], key, connect_command)

    if rc > 0:
        response += "server connecting fail\n"
        return status, response
    else:
        response += "server connecting good\n"

    start_command = 'docker exec ' + name + " /bin/sh -c '" + start_command + "'"
    rc = server_run_cmd(first_node['ip'], first_node['user'], key, start_command)

    if rc > 0:
        response += "server start fail\n"
    else:
        status = True
        response += "server start good\n"

    for node in nodes:
        if node['status'] == 1:
            node['connected'] = 1

    return status, response