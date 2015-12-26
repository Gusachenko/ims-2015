#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys


BUFFER = 4096


def cmd_input(sock):
    try:
        cmd = ''
        print "input command"
        while cmd != 'exit':
            cmd = raw_input('pgluster> ')
            sock.send(cmd)
            data = sock.recv(BUFFER)
            print data
    except:
        cmd = 'exit'
    sock.send(cmd)
    return 0


if __name__ == '__main__':
    try:
        sock = socket.socket()
        sock.connect(('localhost', 8888))
        code = cmd_input(sock)
        sock.close()
    except :
        print "Is 'pglusterd' running?"
        code = 111
    print 'Bye'
    sys.exit(code)