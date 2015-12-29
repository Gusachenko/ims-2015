__author__ = 'Vladislav'
import threading
import paramiko
import yaml
from subprocess import Popen, PIPE
from time import sleep
import sys

DOCKER = 'docker'
VAGRANT = 'vagrant'


def manage_script(args):
    sleep(2)
    child = Popen(args, stdout=PIPE, stderr=PIPE)

    child.communicate()
    rc = child.returncode
    return rc


def up_vagrant(client, web):
    manage_script([VAGRANT, 'halt', '-f'])
    manage_script([DOCKER, 'rm', '-f', client['name']])
    manage_script([DOCKER, 'rm', '-f', web['name']])
    rc = manage_script([VAGRANT, 'up', "--no-parallel"])

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
    codes = []
    if type(cmd) is list:
        for cmd_run in cmd:
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd_run)
            codes.append(ssh_stdout.channel.recv_exit_status())

    else:
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)

    rc = ssh_stdout.channel.recv_exit_status()
    codes.append(rc)
    ssh.close()
    return rc, codes


def link_servers(nodes, name, vol, brick, key):
    response = ''
    status = False
    commands = []
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
    connect_command = 'docker exec ' + name + " /bin/sh -c '" + connect_command + "'"
    start_command = 'docker exec ' + name + " /bin/sh -c '" + start_command + "'"

    commands.append(peer_command)
    commands.append(connect_command)
    commands.append(start_command)

    rc, res = server_run_cmd(first_node['ip'], first_node['name'], key, commands)

    for i, r in enumerate(res):
        if r > 0:
            if i == 0:
                response += "server peer connecting fail\n"
            elif i == 1:
                response += "server connecting fail\n"
            elif i == 2:
                response += "server start fail\n"
            return status, response
        else:
            if i == 0:
                response += "server peer connecting good \n"
            elif i == 1:
                response += "server connecting good\n"
            elif i == 2:
                response += "server start good\n"
    status = True
    for node in nodes:
        if node['status'] == 1:
            node['connected'] = 1

    return status, response


def remove_server(node, name, key):
    command = DOCKER + ' rm -f ' + name
    rc, res = server_run_cmd(node['ip'], node['name'], key, command)


def append_link(node, server, name, vol, brick, key):
    response = ''
    status = False

    commands = []

    peer_command = "gluster peer probe " + node['ip'] + "; "
    connect_command = 'gluster volume add-brick ' + vol + ' ' + node['ip'] + ":" + brick + " force"

    peer_command = 'docker exec ' + name + " /bin/sh -c '" + peer_command + "'"
    connect_command = 'docker exec ' + name + " /bin/sh -c '" + connect_command + "'"

    commands.append(peer_command)
    commands.append(connect_command)

    rc, res = server_run_cmd(server['ip'], server['name'], key, commands)

    for i, r in enumerate(res):
        if r > 0:
            if i == 0:
                response += "server add peer fail\n"
            elif i == 1:
                response += "server connecting fail\n"
            return status, response
        else:
            if i == 0:
                response += "server add peer good\n"
            elif i == 1:
                response += "server connecting good\n"
    status = True

    node['connected'] = 1

    return status, response
