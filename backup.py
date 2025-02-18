#!/usr/bin/python
import hashlib
import logging
import os
import subprocess
import sys
import tempfile


logging.basicConfig(level=logging.INFO)
log = logging.getLogger()
sys.path.append("./supernote-cloud-python")
import supernote


class Supernote(object):
    def __init__(self, username, password):
        self._token = supernote.login(username, password)
        self._id_to_path = {
            0: "",
        }
        self._path_to_id = {
            "": 0,
        }
        self._id_to_stat = {}

    def _cache_id(self, path, ident):
        ident = int(ident)
        self._id_to_path[ident] = path
        self._path_to_id[path] = ident

    def file_list(self, ident=0):
        entries = supernote.file_list(self._token, ident)
        try:
            current_path = self._id_to_path[int(ident)]
        except KeyError:
            pass
        else:
            # Cache identifiers from the result
            for entry in entries:
                self._cache_id(
                    os.path.join(current_path, entry["fileName"]), entry["id"]
                )

        # Cache stat info
        for entry in entries:
            self._id_to_stat[int(entry["id"])] = {
                key: entry[key] for key in ("size", "md5", "createTime", "updateTime")
            }

        return entries

    def stat(self, path=None, ident=0):
        if path is not None:
            ident = self._path_to_id[path]

        return self._id_to_stat[int(ident)]

    def download_file(self, filename, path=None, ident=0):
        if path is not None:
            ident = self._path_to_id[path]

        return supernote.download_file(self._token, ident, filename)

    def walk(self, path="", ident=0):
        if path and ident:
            raise RuntimeError("Both path and identifier specified")

        if not ident:
            try:
                ident = self._path_to_id[path]
            except KeyError:
                raise RuntimeError("Path not previously seen, use identifier instead")

        # List what's in a folder
        entries = self.file_list(ident=ident)

        # Separate folders from files
        folders = []
        files = []
        current_path = path or self._id_to_path[int(ident)]
        for entry in entries:
            if entry["isFolder"] == "Y":
                folders.append(entry)
            else:
                files.append(entry)

        foldernames = [folder["fileName"] for folder in folders]
        yield (current_path, foldernames, [file["fileName"] for file in files])

        # Trim folders in case foldernames was modified by caller
        folders = [folder for folder in folders if folder["fileName"] in foldernames]
        for folder in folders:
            yield from self.walk(ident=folder["id"])


def calculate_md5sum(filename):
    md5 = hashlib.md5()
    with open(filename, "rb") as fp:
        while True:
            data = fp.read()
            if not data:
                break

            md5.update(data)

    return md5.hexdigest()


def sync(sn, destdir):
    # mkdir -p
    components = os.path.split(destdir)
    for ncomp in range(len(components)):
        dir = os.path.join(*components[: ncomp + 1])
        if not dir:
            continue
        try:
            os.mkdir(dir)
        except FileExistsError:
            pass

    for path, dirs, files in sn.walk():
        if path:
            try:
                os.mkdir(os.path.join(destdir, path))
            except FileExistsError:
                pass

        for file in files:
            filename = os.path.join(path, file)
            stat = sn.stat(filename)
            destfile = os.path.join(destdir, filename)
            if "md5" in stat:
                try:
                    md5sum = calculate_md5sum(destfile)
                except FileNotFoundError:
                    pass
                else:
                    if stat["md5"] == md5sum:
                        log.info(f"{filename} already up to date locally")
                        continue

            log.info(f"Downloading {filename}")
            sn.download_file(destfile, path=filename)


def main():
    username = sys.argv[1]
    destdir = sys.argv[2]
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
    sync(sn, destdir)


if __name__ == "__main__":
    main()
