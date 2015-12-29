#!/usr/bin/env python
import json
import os

import sys, time
from pymongo import MongoClient
from src.daemon import Daemon
import socket
import sys
from thread import *
from src.util import *
from src.commands import *
from shutil import move, copy

HOST = ''
PORT = 8888
BUFFER = 4096

STATE_START = 'start'
STATE_SERVER_UP = 'server up'
STATE_SERVER_LINKED = 'server linked'

CLIENT_START_STATE = 'start'
CLIENT_UP_STATE = 'client up'
CLIENT_LINKED_STATE = 'client linked'


class MyDaemon(Daemon):
    nodes = []
    key = ''
    config = {}
    gluster_config = {}
    db = {}
    state = STATE_START
    client_state = CLIENT_START_STATE

    def run(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((HOST, PORT))
            s.listen(10)
            self.preparations()
            while True:
                conn, addr = s.accept()
                start_new_thread(self.client_thread, (conn,))
            s.close()
        except socket.error:
            self.stop()

    def client_thread(self, conn):
        while True:
            try:
                data = str(conn.recv(BUFFER)).lower()
                args = []
                if len(data.split(' ')) > 2:
                    sub_data = data.split(' ')
                    if sub_data[0] == 'server' and sub_data[1] == 'add':
                        data = sub_data[0] + " " + sub_data[1]
                        for arg in sub_data[2:]:
                            args.append(arg)

                if data == 'help':
                    reply = {'type': 1, 'msg': cmd_help()}
                elif data == 'check':
                    reply = {'type': 1, 'msg': 'done'}
                elif data == 'server state':
                    reply = {'type': 1, 'msg': self.state}
                elif data == 'client state':
                    reply = {'type': 1, 'msg': self.client_state}
                elif data == 'server status':
                    reply = {'type': 1, 'msg': cmd_server_status(self.nodes)}
                elif data == "server add":
                    collection = self.db[self.config['mongo']['server_collection']]
                    res = collection.find_one(dict(ip=args[1]))
                    if res is not None:
                        reply = {'type': 1, 'msg': "already exist " + args[1]}
                        continue
                    collection.save({
                        "name": args[0],
                        "ip": args[1]
                    })
                    r_node = {}
                    r_node['name'] = str(args[0])
                    r_node['ip'] = str(args[1])
                    r_node['status'] = 0
                    r_node['connected'] = 0
                    if self.state == STATE_START:
                        reply = {'type': 1, 'msg': "add server " + args[1]}
                        self.send(conn, reply)
                        self.nodes.append(r_node)
                        continue

                    if self.state != STATE_START:
                        reply = {'type': 0, 'msg': "up node " + args[1]}
                        self.send(conn, reply)
                        up_count, msg = cmd_server_up(
                            self.gluster_config['server']['name'],
                            self.gluster_config['server']['image'],
                            self.key,
                            [r_node],
                        )

                        if self.state == STATE_SERVER_UP:
                            self.nodes.append(r_node)
                        if up_count > 0:
                            reply = {'type': 0, 'msg': msg}
                            self.send(conn, reply)

                        else:
                            reply = {'type': 1, 'msg': msg}
                            self.send(conn, reply)
                            continue

                        if self.state == STATE_SERVER_LINKED:
                            sleep(2)
                            reply = {'type': 0, 'msg': "start linking " + args[1]}
                            self.send(conn, reply)
                            for node in self.nodes:
                                if node['status'] == 1:
                                    server = node
                            status, response = append_link(
                                node=r_node,
                                server=server,
                                name=self.gluster_config['server']['name'],
                                vol=self.gluster_config['vol'],
                                brick=self.gluster_config['brick'],
                                key=self.key
                            )
                            self.nodes.append(r_node)

                            reply = {'type': 1, 'msg': response}

                elif data == 'client up':
                    if self.state != STATE_SERVER_LINKED:
                        reply = {'type': 1, 'msg': "Server is not up"}
                        self.send(conn, reply)
                        continue
                    if self.client_state == CLIENT_LINKED_STATE:
                        reply = {'type': 1, 'msg': "Client linked"}
                        self.send(conn, reply)
                        continue
                    if self.client_state == CLIENT_START_STATE:
                        copy(self.gluster_config['vagrant_file'], '/tmp/Vagrantfile')
                        os.chdir('/tmp/')
                        status, msg = cmd_client_up(
                            self.gluster_config['client'],
                            self.gluster_config['web']
                        )
                        os.chdir('/')

                        if status:
                            self.client_state = CLIENT_UP_STATE
                            reply = {'type': 0, 'msg': msg}
                            self.send(conn, reply)
                        else:
                            reply = {'type': 1, 'msg': msg}
                            self.send(conn, reply)
                            continue

                    if self.client_state == CLIENT_UP_STATE:
                        sleep(2)
                        status = cmd_client_link(
                            self.gluster_config['vol'],
                            self.gluster_config['client']['name'],
                            self.nodes,
                        )
                        if status:
                            self.client_state = CLIENT_LINKED_STATE
                            reply = {'type': 1, 'msg': "Link Done"}
                        else:
                            reply = {'type': 1, 'msg': "Link failed"}
                            self.send(conn, reply)
                            continue

                elif data == 'server up':
                    if len(self.nodes) == 0:
                        reply = {'type': 1, 'msg': "Add server, no servers"}
                        self.send(conn, reply)
                        continue
                    if self.state == STATE_SERVER_LINKED:
                        reply = {'type': 1, 'msg': "Server is up"}
                        self.send(conn, reply)
                        continue

                    if self.state == STATE_START:
                        reply = {'type': 0, 'msg': "start up servers"}
                        self.send(conn, reply)
                        up_count, msg = cmd_server_up(
                            self.gluster_config['server']['name'],
                            self.gluster_config['server']['image'],
                            self.key,
                            self.nodes,
                        )

                        if up_count > 0:
                            reply = {'type': 0, 'msg': msg}
                            self.send(conn, reply)

                            self.state = STATE_SERVER_UP
                        else:
                            reply = {'type': 1, 'msg': msg}
                            self.send(conn, reply)
                            continue

                    sleep(2)
                    if self.state == STATE_SERVER_UP:
                        reply = {'type': 0, 'msg': "start linking"}
                        self.send(conn, reply)

                        status, response = link_servers(
                            self.nodes,
                            self.gluster_config['server']['name'],
                            self.gluster_config['vol'],
                            self.gluster_config['brick'],
                            self.key
                        )
                        if status:
                            self.state = STATE_SERVER_LINKED
                        reply = {'type': 1, 'msg': response}

                    else:
                        reply = {'type': 1, 'msg': "Wrong state restart daemon"}

                elif data == 'exit':
                    break
                else:
                    reply = {'type': 1, 'msg': 'No command %s found, use help' % str(data)}
                self.send(conn, reply)
            except:
                sleep(2)
                self.send(conn, {'type': 1, 'msg': "error"})
        conn.close()

    @staticmethod
    def send(conn, message):
        conn.send(
            json.dumps(message)
        )

    def preparations(self):
        self.config = get_containers_data()
        self.gluster_config = self.config['glusterfs']
        self.key = load_key(self.gluster_config['server']['key'])
        self.db = MongoClient(
            self.config['mongo']['host'],
            self.config['mongo']['port'])[self.config['mongo']['name']]
        collection = self.db[self.config['mongo']['server_collection']]
        res = collection.find({})
        if res is not None:
            for node in res:
                r_node = {}
                r_node['name'] = str(node['name'])
                r_node['ip'] = str(node['ip'])
                r_node['status'] = 0
                r_node['connected'] = 0
                self.nodes.append(r_node)


if __name__ == "__main__":
    daemon = MyDaemon('/tmp/pglusterd.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)