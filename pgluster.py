#!/usr/bin/env python
import re

import socket
import sys
import json

BUFFER = 4096


def cmd_input(sock):
    try:
        cmd = ''
        print "input command"
        while cmd != 'exit':
            cmd = str(raw_input('pgluster> '))
            if len(cmd) != 0:
                sock.send(cmd)
                while True:
                    data = sock.recv(BUFFER)
                    try:
                        json_acceptable_string = data.replace("'", "\"")
                        res = json.loads(json_acceptable_string, "utf-8")
                        print str(res['msg'])
                        if res['type'] == 1:
                            break
                    except:
                        print data
                        break
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
    except:
        print "Is 'pglusterd' running?"
        code = 111
    print '\nBye'
    sys.exit(code)