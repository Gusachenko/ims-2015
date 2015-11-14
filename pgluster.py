#!/usr/bin/python
# coding=utf-8

# docker inspect -format '{{ .NetworkSettings.IPAddress }}'
# Задачи
# 1 поднять вагрант
# 2 по конфигу собрать всё вкучу
# 3 связать всё это дело
# 4 ???
# 5 profit

import yaml
from subprocess import Popen, PIPE
import datetime
import sys
import os
from time import sleep
import time
import re

VAGRANT = 'vagrant'
DOCKER = 'docker'


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


def up_vagrant():
    rc = manage_script([VAGRANT, 'up', "--no-parallel"])

    return rc


def link_servers(containers, gluster_data):
    ips = []
    i = 0
    while i < containers['count']:
        i += 1
        container_name = containers['name'] + "-" + str(i)
        child = Popen([DOCKER, 'inspect', '--format', '\'{{ .NetworkSettings.IPAddress }}\'', container_name],
                      stdout=PIPE, stderr=PIPE)

        output = child.stdout.read()
        ips.append(output
                   .rstrip()
                   .replace('\'', '')
                   )

    peer_command = ''
    start_command = 'gluster volume start ' + gluster_data['gluster_vol']
    connect_command = 'gluster volume create ' \
                      + gluster_data['gluster_vol'] \
                      + ' replica ' \
                      + str(containers['count']) \
                      + ' transport tcp '
    for ip in ips:
        peer_command += "gluster peer probe " + ip + "; "
        connect_command += " " + ip + ":" + gluster_data['gluster_brick']

    connect_command += " force"

    first_name = containers['name'] + '-' + '1'

    rc = manage_script([DOCKER, 'exec', first_name, '/bin/sh', '-c', peer_command],True)
    print "connecting peers return code = %d" % rc

    rc = manage_script([DOCKER, 'exec', first_name, '/bin/sh', '-c', connect_command],True)
    print "connecting volumes return code = %d" % rc

    rc = manage_script([DOCKER, 'exec', first_name, '/bin/sh', '-c', start_command],True)
    print "start command return code = %d" % rc

    return ips[0]


def connect_client(server, client, gluster_data):
    run_command = "mount -t glusterfs " + server + ":/" + gluster_data['gluster_vol'] + " /mnt/glusterfs"

    rc = manage_script([DOCKER, 'exec', client['name'], '/bin/sh', '-c', run_command],True)
    print "connect return code = %d" % rc
    return rc


def stop_all(containers):
    manage_script([VAGRANT, 'halt', '-f'],True)

    servers = containers['data']['server']
    i = 0
    while i < servers['count']:
        i += 1
        container_name = servers['name'] + "-" + str(i)
        manage_script([DOCKER, 'rm', '-f', container_name])
    manage_script([DOCKER, 'rm', '-f', containers['data']['client']['name']])
    manage_script([DOCKER, 'rm', '-f', containers['data']['web']['name']])


def get_containers_data():
    with open("containers.yml", 'r') as stream:
        return yaml.load(stream)


def main():
    gluster_data = get_containers_data()
    print "stop all"
    stop_all(gluster_data)
    servers = gluster_data['data']['server']
    client = gluster_data['data']['client']
    web_proxy = gluster_data['data']['web']
    print "starting app"
    rc = up_vagrant()
    if rc == 0:
        print "start ok, link"
        server_ip = link_servers(servers, gluster_data['gluster'])
        rc = connect_client(server_ip, client, gluster_data['gluster'])
        if rc == 0:
            print "All OK, glusterfs client listen on port %s" % web_proxy['port']
            return 0
        else:
            print "Client link fail\n"
        print "start fail stop all"
        stop_all(gluster_data)
        return 1

if __name__ == '__main__':
    main()