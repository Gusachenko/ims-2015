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


def manage_script(args):
    sleep(2)
    child = Popen(args, stdout=PIPE, stderr=PIPE)
    output = child.stdout.read()
    err = child.stderr.read()
    print output

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

    print ips
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

    rc = manage_script([DOCKER, 'exec', first_name, '/bin/sh', '-c', peer_command])
    print "connecting peers return code = %d" % rc

    rc = manage_script([DOCKER, 'exec', first_name, '/bin/sh', '-c', connect_command])
    print "connecting volumes return code = %d" % rc

    rc = manage_script([DOCKER, 'exec', first_name, '/bin/sh', '-c', start_command])
    print "start command return code = %d" % rc

    return ips[0]


def connect_client(server, client, gluster_data):
    run_command = "mount -t glusterfs " + server + ":/" + gluster_data['gluster_vol'] + " /mnt/glusterfs"


    rc = manage_script([DOCKER, 'exec', "glusterfs-client", '/bin/sh', '-c', run_command])
    print "connect return code = %d" % rc


def stop_all(containers):
    for item in containers['data']:
        i = 0
        while i < item['count']:
            i += 1
            container_name = item['name'] + "-" + str(i)
            manage_script([DOCKER, 'rm', '-f', container_name])
        #manage_script([DOCKER, 'rm', '-f', "web-gluster-client"])
        manage_script([DOCKER, 'rm', '-f', "glusterfs-client"])
        manage_script([DOCKER, 'rm', '-f', "nginx-gluster"])
    return 1


def get_containers_data():
    with open("containers.yml", 'r') as stream:
        return yaml.load(stream)


def main():
    server = []
    client = []

    gluster_data = get_containers_data()
    print "stop all"
    stop_all(gluster_data)

    for item in gluster_data['data']:
        if item['type'] == 'server':
            server = item
        else:
            client = item

    print "starting app"
    rc = up_vagrant()
    if rc == 0:
        print "start ok, link"
        server_ip = link_servers(server, gluster_data['gluster'])
        connect_client(server_ip, client, gluster_data['gluster'])
    else:
        print "start fail stop all"
        stop_all(gluster_data)

    return 1


if __name__ == '__main__':
    main()