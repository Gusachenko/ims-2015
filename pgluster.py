#!/usr/bin/python
# coding=utf-8

import threading
import paramiko
import yaml
from subprocess import Popen, PIPE
from time import sleep
import sys

DOCKER = 'docker'
VAGRANT = 'vagrant'


class ServerUpThread(threading.Thread):
    def __init__(self, thread_id, credentials, name, image):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.result = False
        self.credentials = credentials
        self.name = name
        self.image = image

    def return_exit_code(self):
        return self.result

    def run(self):
        print "Starting " + self.name + " id " + str(self.thread_id)
        try:
            exit_code = up_server(
                self.credentials['ip'],
                self.credentials['user'],
                self.credentials['key'],
                self.name,
                self.image
            )
            if exit_code is 0:
                self.result = True
            print self.name + " id " + str(self.thread_id) + " exit code " + str(exit_code)
        except:
            print self.name + " id " + str(self.thread_id) + " exit code " + str(0)



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
    manage_script([VAGRANT, 'halt', '-f'], True)
    rc = manage_script([VAGRANT, 'up', "--no-parallel"], True)

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
    ssh.connect(host, username=user, pkey=rsa_key, banner_timeout=120, timeout=120)

    # stop container
    cmd = DOCKER + " rm -f " + name
    ssh.exec_command(cmd)

    # run container
    cmd = DOCKER \
          + " run -d --privileged=true -v /mnt/gluster_volume:/gluster_volume --name='" \
          + name \
          + "' --net='host' " \
          + image

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

    return rc


def connect_client(server, client, gluster_data):
    run_command = "mount -t glusterfs " + server + ":/" + gluster_data['vol'] + " /mnt/glusterfs"

    rc = manage_script([DOCKER, 'exec', client['name'], '/bin/sh', '-c', run_command], True)
    print "connect return code = %d" % rc
    return rc


def up():
    gluster_data = get_containers_data()
    server_data = gluster_data['glusterfs']['server']
    client_data = gluster_data['glusterfs']['client']
    gl_data = gluster_data['glusterfs']
    threads = []

    i = 0
    for node in server_data['credentials']:
        i += 1
        thread = ServerUpThread(i, node, server_data['name'], server_data['image'])
        thread.start()
        threads.append(thread)

    res = True
    for t in threads:
        t.join()
        if t.return_exit_code() is False:
            res = False
            print "Node up fail"
    if res is False:
        return 1

    print "Servers Up done"
    print "Start Linking"

    rc = link_servers(
        server_data['credentials'],
        server_data['name'],
        gl_data['vol'],
        gl_data['brick']
    )
    if rc > 0:
        print "client up fail"
        return 1
    print "Up client"
    rc = up_vagrant()
    if rc > 0:
        print "client up fail"
        return 1

    print "Link Client"

    rc = connect_client(server_data['credentials'][0]['ip'], client_data, gl_data)
    if rc > 0:
        print "client link fail"
        return 1

    print "Up Done!"

def cmd_input():
    try:
        cmd = ''
        print "input command"
        while cmd != 'exit':
            cmd = raw_input('pgluster> ')
            if cmd == 'up':
                up()
            elif cmd == 'help':
                cmd_help()
            elif cmd == 'exit':
                cmd_exit(0)
            else:
                print "No command '%s' found, use help" % str(cmd)
    except KeyboardInterrupt:
        cmd_exit(0)


def cmd_exit(code):
    print '\nBye'
    sys.exit(code)


def cmd_help():
    print 'up  -- up server and client'


if __name__ == '__main__':
    cmd_input()