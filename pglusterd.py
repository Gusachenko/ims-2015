#!/usr/bin/env python
import os

import sys, time
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
    nodes = {}
    key = ''
    config = {}
    gluster_config = {}
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
                if data == 'help':
                    reply = {'type': 1, 'msg': cmd_help()}
                elif data == 'check':
                    reply = {'type': 1, 'msg': 'done'}
                elif data == 'path':
                    reply = {'type': 1, 'msg': os.path.dirname(os.path.realpath(__file__))}
                elif data == 'state':
                    reply = {'type': 1, 'msg': self.state}
                elif data == 'client state':
                    reply = {'type': 1, 'msg': self.client_state}
                elif data == 'server status':
                    reply = {'type': 1, 'msg': cmd_server_status(self.nodes)}
                elif data == 'client up':
                    if self.state != STATE_SERVER_LINKED:
                        reply = str({'type': 1, 'msg': "Server is not up"})
                        conn.send(reply)
                        continue
                    if self.client_state == CLIENT_LINKED_STATE:
                        reply = str({'type': 1, 'msg': "Client linked"})
                        conn.send(reply)
                        continue
                    if self.client_state == CLIENT_START_STATE:
                        copy(self.gluster_config['vagrant_file'], '/tmp/Vagrantfile')
                        os.chdir('/tmp/')
                        status, msg = cmd_client_up()
                        os.chdir('/')

                        if status:
                            self.client_state = CLIENT_UP_STATE
                            reply = str({'type': 0, 'msg': msg})
                            conn.send(reply)
                        else:
                            reply = str({'type': 1, 'msg': msg})
                            conn.send(reply)
                            continue

                    if self.client_state == CLIENT_UP_STATE:
                        status = cmd_client_link(
                            self.gluster_config['vol'],
                            self.gluster_config['client']['name'],
                            self.nodes,
                        )
                        if status:
                            self.client_state = CLIENT_LINKED_STATE
                            reply = str({'type': 1, 'msg': "Link Done"})
                        else:
                            reply = str({'type': 1, 'msg': "Link failed"})
                            conn.send(reply)
                            continue

                elif data == 'server up':
                    if self.state == STATE_SERVER_LINKED:
                        reply = str({'type': 1, 'msg': "Server is up"})
                        conn.send(reply)
                        continue
                    if self.state == STATE_START:
                        reply = str({'type': 0, 'msg': "start up servers"})
                        conn.send(reply)
                        up_count, msg = cmd_server_up(
                            self.gluster_config['server']['name'],
                            self.gluster_config['server']['image'],
                            self.key,
                            self.nodes,
                        )

                        if up_count > 0:
                            reply = {'type': 0, 'msg': msg}
                            conn.send(str(reply))

                            self.state = STATE_SERVER_UP
                        else:
                            reply = {'type': 1, 'msg': msg}
                            conn.send(str(reply))
                            continue

                    sleep(2)
                    if self.state == STATE_SERVER_UP:
                        reply = {'type': 0, 'msg': "start linking"}
                        conn.send(str(reply))

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
                conn.send(str(reply))
            except:
                conn.send(str({'type': 1, 'msg': "error"}))
        conn.close()

    def preparations(self):
        self.config = get_containers_data()
        self.gluster_config = self.config['glusterfs']
        self.key = load_key(self.gluster_config['server']['key'])
        self.nodes = self.gluster_config['server']['credentials']
        for node in self.nodes:
            node['status'] = 0
            node['connected'] = 0


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