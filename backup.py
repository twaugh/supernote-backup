#!/usr/bin/python
import logging
import os
import subprocess
import sys
import tempfile


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()
sys.path.append("./supernote-cloud-python")
import supernote


class Supernote(object):
    def __init__(self, username, password):
        self._token = supernote.login(username, password)

    def file_list(self, directory=0):
        return supernote.file_list(self._token, directory)

    def download_file(self, ident, filename):
        return supernote.download_file(self._token, ident, filename)


def recurse_file_tree(sn, file_list):
    for entry in file_list:
        fileName = entry["fileName"]
        if entry["isFolder"] == "Y":
            try:
                os.mkdir(fileName)
            except FileExistsError:
                pass

            os.chdir(fileName)
            log.debug(f"recurse into {fileName}")
            subdir = sn.file_list(directory=entry["id"])
            recurse_file_tree(sn, subdir)
        else:
            log.debug(f"download {fileName}")
            with tempfile.NamedTemporaryFile(dir=".", delete=False) as tmpf:
                sn.download_file(entry["id"], tmpf.name)
                os.rename(tmpf.name, fileName)


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
    recurse_file_tree(sn, top)


if __name__ == "__main__":
    main()
