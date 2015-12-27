__author__ = 'Vladislav'
from serverUpThread import ServerUpThread
from util import *


def cmd_help():
    help_str = 'server up - for up servers \n' \
               'server status - return servers status \n' \
               'server count - return online servers count \n' \
               'server add %username% %ip% - add new server and connect it if state is linked return status \n' \
               'state - get state \n' \
               'client up - for up client \n'
    return help_str


def cmd_server_up(name, image, key, nodes):
    threads = []
    response = ''
    # clear
    i = 0
    for node in nodes:
        i += 1
        thread = ServerUpThread(i, name, image, key, node)
        thread.start()
        threads.append(thread)

    up_count = 0
    for t in threads:
        t.join()
        t_id, t_code = t.return_code()
        if t_code is False:
            nodes[t_id - 1]['status'] = 0
            response += nodes[t_id - 1]['ip'] + " up fail \n"
        else:
            up_count += 1
            nodes[t_id - 1]['status'] = 1
            response += nodes[t_id - 1]['ip'] + " up done \n"

    return up_count, response


def cmd_link_server(vol, brick, name, key, nodes):
    return link_servers(nodes, name, vol, brick, key)


def cmd_server_status(nodes):
    response = ''
    for node in nodes:
        if node['status'] == 0:
            response += node['ip'] + ' is offline \n'
        else:
            response += node['ip'] + ' is online \n'
            if node['connected'] == 1:
                response += "\t" + node['ip'] + ' is connected \n'
    return response
