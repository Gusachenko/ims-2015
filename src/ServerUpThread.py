from util import *


class ServerUpThread(threading.Thread):
    def __init__(self, thread_id, name, image, key, node):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.result = False
        self.key = key
        self.node = node
        self.name = name
        self.image = image

    def return_code(self):
        return self.thread_id, self.result

    def run(self):
        try:
            run_cmd = DOCKER \
                + " run -d --privileged=true -v /mnt/gluster_volume:/gluster_volume --name='" \
                + self.name \
                + "' --net='host' " \
                + self.image
            cmd = [
                DOCKER + " rm -f " + self.name,
                run_cmd
            ]

            exit_code, codes = server_run_cmd(
                self.node['ip'],
                self.node['name'],
                self.key,
                cmd,
            )
            if not(codes[1] > 0):
                self.result = True
                self.node['status'] = 1
        except:
            self.node['status'] = 0