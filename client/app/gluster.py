import hashlib
import os.path
from random import randint


def md5_file(f_name):
    h = hashlib.md5()
    with open(f_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), "b"):
            h.update(chunk)
    return h.hexdigest()


def md5_data(data):
    h = hashlib.md5()
    h.update(data)
    return h.hexdigest()


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
    local_dir = os.path.dirname(os.path.realpath(__file__))
    full_file_name = local_dir + "/" + h.hexdigest()
    if not os.path.isfile(full_file_name):
        os.rename(tmp_name, full_file_name)
    os.remove(tmp_name)
    return h


def get_file(file_name):
    f = open(file_name, 'rb')
    return f
