import hashlib
import json
import os
from random import randint
from shutil import move
from os import listdir
from os.path import isfile, join
import time

VOLUME_DIR = os.environ.get('SAVE_DIR', "/mnt/glusterfs")


def save_file(stream, filename):
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
    full_file_name = join(VOLUME_DIR, h.hexdigest())
    now = int(time.time())
    if not os.path.isfile(full_file_name):
        move(tmp_name, full_file_name)

        meta_data = {
            'filename': [filename],
            'oid': h.hexdigest(),
            'created': now,
            'updated': now
        }

        with open(full_file_name + '.meta', 'w+') as meta:
            meta.write(json.dumps(
                meta_data
            ))
    else:
        with open(full_file_name + '.meta', 'r+') as meta:
            raw_meta = meta.read()
            meta_data = json.loads(raw_meta, 'utf-8')
            if filename not in meta_data['filename']:
                meta_data['filename'].append(filename)
                meta_data['updated'] = now
                meta.seek(0)
                meta.write(
                    json.dumps(
                        meta_data
                    )
                )
                meta.truncate()
                meta.close()
        os.remove(tmp_name)
    return h.hexdigest()


def remove_file(oid):
    try:
        os.remove(VOLUME_DIR + "/" + oid)
        os.remove(VOLUME_DIR + "/" + oid + '.meta')
        return True
    except:
        return False


def file_list():
    result = []
    files = [f for f in listdir(VOLUME_DIR) if isfile(join(VOLUME_DIR, f))]
    for f in files:
        filename, file_extension = os.path.splitext(f)
        if file_extension == '.meta':
            with open(join(VOLUME_DIR, f), "r") as meta_file:
                meta_data = meta_file.read()
                result.append(json.loads(meta_data, "utf-8"))
    return result


def get_file(file_name):
    f = open(VOLUME_DIR + '/' + file_name, 'rb')
    return f
