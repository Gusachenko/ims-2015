#!/usr/bin/env python

import sys, time
from src.daemon import Daemon
import socket
import sys
from thread import *
from src.util import *
from src.commands import *

HOST = ''
PORT = 8888
BUFFER = 4096

nodes = []
key = ''
config = ''
gluster_config = ''


class MyDaemon(Daemon):
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

    @staticmethod
    def client_thread(conn):
        while True:
            data = conn.recv(BUFFER)
            if data == 'up':
                reply = 'ip'
            elif data == 'exit':
                break
            else:
                reply = "No command '%s' found, use help" % str(data)
            conn.sendall(reply)
        conn.close()

    @staticmethod
    def preparations():
        config = get_containers_data()
        gluster_config = config['glusterfs']
        key = load_key(gluster_config['server']['key'])
        nodes = gluster_config['server']['credentials']
        for node in nodes:
            node['status'] = 0


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