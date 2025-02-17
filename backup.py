#!/usr/bin/python
import logging
import subprocess
import sys


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()
sys.path.append("./supernote-cloud-python")
import supernote


class Supernote(object):
    def __init__(self, username, password):
        self._token = supernote.login(username, password)

    def file_list(self, directory=0):
        return supernote.file_list(self._token, directory)


def get_file_tree(sn, file_list):
    file_tree = {}
    for entry in file_list:
        fileName = entry['fileName']
        if entry['isFolder'] == 'Y':
            log.debug(f"recurse into {fileName}")
            subdir = sn.file_list(directory=entry['id'])
            file_tree[fileName] = {
                'type': 'folder',
                'contents': get_file_tree(sn, subdir),
            }
        else:
            file_tree[fileName] = {
                'type': 'file',
            }
    return file_tree


def main():
    username = sys.argv[1]
    sp = subprocess.Popen(
        ["pass", f"supernote/{username}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    (stdout, stderr) = sp.communicate()
    if sp.returncode != 0:
        log.error(f"Configure pass with supernote/{username}")
    if not stdout:
        log.error(stderr)
    password = stdout.splitlines()[0].decode()
    sn = Supernote(username, password)
    
    top = sn.file_list()
    file_tree = get_file_tree(sn, top)
    print(file_tree)



if __name__ == "__main__":
    main()
