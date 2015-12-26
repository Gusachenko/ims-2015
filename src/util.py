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

    rsa_key = paramiko.RSAKey.from_private_key_file(key)
    ssh.connect(host, username=user, pkey=rsa_key, banner_timeout=120, timeout=120)

    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)

    rc = ssh_stdout.channel.recv_exit_status()
    ssh.close()
    return rc


def link_servers(nodes, name, vol, brick):
    peer_command = ''
    start_command = 'gluster volume start ' + vol
    connect_command = 'gluster volume create ' \
                      + vol \
                      + ' transport tcp '

    for node in nodes:
        peer_command += "gluster peer probe " + node['ip'] + "; "
        connect_command += " " + node['ip'] + ":" + brick

    connect_command += " force"
    first_node = nodes[0]
    peer_command = 'docker exec ' + name + " /bin/sh -c '" + peer_command + "'"
    rc = exec_ssh_docker(first_node['ip'], name, peer_command)
    print "connecting peers return code = %d" % rc

    rc = exec_ssh_docker(first_node, name, connect_command)
    print "volume create command return code = %d" % rc

    rc = exec_ssh_docker(first_node, name, start_command)
    print "start return code = %d" % rc

    return rc