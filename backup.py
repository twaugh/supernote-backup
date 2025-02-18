#!/usr/bin/python
import hashlib
import logging
import os
import string
import subprocess
import sys
import tempfile
import urllib.parse


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), "supernote-cloud-python"))
import supernote


class Supernote(object):
    # We need to percent-encode "/" to describe remote paths, since we're representing
    # folders like a filesystem with "/" as a separator
    _SAFE_CHARS = " \t" + "".join(set(string.punctuation) - {"/"})

    def __init__(self, username, password):
        self._token = supernote.login(username, password)

        # Cache the mapping between identifiers and full paths
        self._id_to_path = {}
        self._path_to_id = {}
        self._cache_id("", 0)

        # Also cache file information
        self._id_to_stat = {}

    @classmethod
    def quote(cls, path):
        return urllib.parse.quote(path, safe=cls._SAFE_CHARS)

    @staticmethod
    def unquote(path):
        return urllib.parse.unquote(path)

    def _cache_id(self, path, ident):
        ident = int(ident)
        self._id_to_path[ident] = path
        self._path_to_id[path] = ident
        log.info(self._path_to_id)

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
                    os.path.join(current_path, Supernote.quote(entry["fileName"])),
                    entry["id"],
                )

        # Cache file information
        for entry in entries:
            self._id_to_stat[int(entry["id"])] = {
                key: entry[key] for key in ("size", "md5", "createTime", "updateTime")
            }

        return entries

    def stat_path(self, path):
        ident = self._path_to_id[path]
        return self.stat_id(ident)

    def stat_id(self, ident):
        return self._id_to_stat[int(ident)]

    def upload_file_path(self, src, dstpath):
        try:
            dstident = self._path_to_id[dstpath]
        except KeyError:
            raise RuntimeError(
                "Destination path not previously seen, use identifer instead"
            )

        return self.upload_file_id(self, src, ident=dstident)

    def upload_file_id(self, src, ident=0):
        return supernote.upload_file(self._token, src, directory=dstident)

    def download_file_path(self, path, filename):
        ident = self._path_to_id[path]
        return self.download_file_id(ident, filename)

    def download_file_id(self, ident, filename):
        return supernote.download_file(self._token, ident, filename)

    def walk_path(self, path=""):
        try:
            ident = self._path_to_id[path]
        except KeyError:
            raise RuntimeError("Path not previously seen, use identifier instead")

        return self.walk_id(self, ident=ident)

    def walk_id(self, ident=0):
        # List what's in a folder
        entries = self.file_list(ident=ident)

        # Separate folders from files
        folders = []
        files = []
        current_path = self._id_to_path[int(ident)]
        for entry in entries:
            if entry["isFolder"] == "Y":
                folders.append(entry)
            else:
                files.append(entry)

        foldernames = [Supernote.quote(folder["fileName"]) for folder in folders]
        yield (
            current_path,
            foldernames,
            [Supernote.quote(file["fileName"]) for file in files],
        )

        # Trim folders in case foldernames was modified by caller
        folders = [
            folder
            for folder in folders
            if Supernote.quote(folder["fileName"]) in foldernames
        ]
        for folder in folders:
            yield from self.walk_id(ident=folder["id"])

    def walk(self):
        return self.walk_id()


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
            stat = sn.stat_path(filename)
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
            sn.download_file_path(filename, destfile)


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
