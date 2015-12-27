import hashlib
import os
from random import randint
from shutil import move,copy

VOLUME_DIR = os.environ.get('SAVE_DIR', "/mnt/glusterfs")


def save_file(stream):
    tmp_name = "/tmp/gluster_temp_steam_file" + str(randint(0, 255))
    with open(tmp_name, "wb") as f:
        h = hashlib.md5()
        chunk_size = 4096
        while True:
            chunk = stream.read(chunk_size)
            if len(chunk) == 0:
                break
            f.write(chunk)
            h.update(chunk)
    full_file_name = VOLUME_DIR + "/" + h.hexdigest()
    if not os.path.isfile(full_file_name):
        move(tmp_name, full_file_name)
    else:
        os.remove(tmp_name)
    return h.hexdigest()


def get_file(file_name):
    f = open(VOLUME_DIR + '/' + file_name, 'rb')
    return f
