#!/usr/bin/python
# coding=utf-8

# docker inspect -format '{{ .NetworkSettings.IPAddress }}'
# Задачи
# 1 по ssh поключиться к машинам по конфигу
# 2 на каждой поднять сервер
# 3 связать всё это дело
# 4 ???
# 5 profit
import argparse
import threading
import paramiko
import yaml
from subprocess import Popen, PIPE
from time import sleep

DOCKER = 'docker'
VAGRANT = 'vagrant'


class ServerUpThread(threading.Thread):
    def __init__(self, thread_id, credentials, name, image):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.credentials = credentials
        self.name = name
        self.image = image

    def run(self):
        print "Starting " + self.name + " id " + str(self.thread_id)
        exit_code = up_server(
            self.credentials['ip'],
            self.credentials['user'],
            self.credentials['key'],
            self.name,
            self.image
        )
        print self.name + " id " + str(self.thread_id) + " exit code " + str(exit_code)


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


def get_containers_data():
    with open("containers.yml", 'r') as stream:
        return yaml.load(stream)


def up_vagrant():
    rc = manage_script([VAGRANT, 'up', "--no-parallel"])

    return rc


def exec_ssh_docker(node, name, cmd):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(
        paramiko.AutoAddPolicy()
    )
    rsa_key = paramiko.RSAKey.from_private_key_file(node['key'])
    ssh.connect(node['ip'], username=node['user'], pkey=rsa_key)

    cmd = 'docker exec ' + name + " /bin/sh -c '" + cmd + "'"

    print cmd

    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)

    for line in ssh_stdout:
        print '... ' + line.strip('\n')
    for line in ssh_stderr:
        print '... ' + line.strip('\n')

    ssh.close()
    return ssh_stdout.channel.recv_exit_status()


def up_server(host, user, key, name, image):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(
        paramiko.AutoAddPolicy()
    )
    rsa_key = paramiko.RSAKey.from_private_key_file(key)
    ssh.connect(host, username=user, pkey=rsa_key)

    # stop container
    cmd = DOCKER + " rm -f " + name
    ssh.exec_command(cmd)

    # run container
    cmd = DOCKER + " run -d --privileged=true -v /mnt/gluster_volume:/gluster_volume --name='" + name + "' --net='host' " + image

    print cmd

    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)

    rc = ssh_stdout.channel.recv_exit_status()
    ssh.close()
    return rc


def link_servers(nodes, name, vol, brick):
    peer_command = ''
    start_command = 'gluster volume start ' + vol
    connect_command = 'gluster volume create ' \
                      + vol \
                      + ' replica ' \
                      + '2' \
                      + ' transport tcp '

    for node in nodes:
        peer_command += "gluster peer probe " + node['ip'] + "; "
        connect_command += " " + node['ip'] + ":" + brick

    connect_command += " force"
    first_node = nodes[0]

    rc = exec_ssh_docker(first_node, name, peer_command)
    print "connecting peers return code = %d" % rc

    rc = exec_ssh_docker(first_node, name, connect_command)
    print "volume create command return code = %d" % rc

    rc = exec_ssh_docker(first_node, name, start_command)
    print "start return code = %d" % rc


def up():
    gluster_data = get_containers_data()
    server_data = gluster_data['glusterfs']['server']
    gl_data = gluster_data['glusterfs']
    threads = []

    i = 0
    for node in server_data['credentials']:
        i += 1
        thread = ServerUpThread(i, node, server_data['name'], server_data['image'])
        thread.start()
        threads.append(thread)

    for t in threads:
        t.join()
    print "Servers Up done"
    print "Start Linking"

    link_servers(
        server_data['credentials'],
        server_data['name'],
        gl_data['vol'],
        gl_data['brick']
    )
    print "Up client"

    up_vagrant()

    print "Exiting Main Thread"

    # print up_server(node['ip'], node['user'], node['key'], server_data['name'], server_data['image'])

    # here we need to add some cheks
    # node = "192.168.94.133"
    # user = "user"
    # ssh_key = "key/open_key"
    #
    # ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('docker')
    # ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('docker')
    #
    # #ssh_stdout.channel.recv_exit_status()
    # for line in ssh_stdout:
    # print '... ' + line.strip('\n')
    # ssh.close()

    return 1


if __name__ == '__main__':
    # here will be args
    if True:
        up()