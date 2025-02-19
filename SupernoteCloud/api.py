#!/usr/bin/python
import logging
import os
import string
import sys
import urllib.parse


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), "../supernote-cloud-python"))
import supernote


class Client(object):
    """
    Supernote Cloud client class

    This class provides methods for interacting with Supernote Cloud. It provides
    an interface similar to a filesystem, including methods which act
    similarly to os.walk(), as well as for uploading and downloading files,
    and fetching metadata.

    Because Supernote Cloud files and folders can use "/" in their names,
    methods are provided to make these usable as local filenames (by quoting).

    Files and folders can be referenced using their unique identifiers,
    or by full "/"-separated pathname (if they have previously been seen).
    """

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
        """
        Convert a Supernote-native filename into a pathname.
        """

        return urllib.parse.quote(path, safe=cls._SAFE_CHARS)

    def _cache_id(self, path, ident):
        ident = int(ident)
        self._id_to_path[ident] = path
        self._path_to_id[path] = ident

    def _file_list(self, ident=0):
        entries = supernote.file_list(self._token, ident)
        try:
            current_path = self._id_to_path[int(ident)]
        except KeyError:
            pass
        else:
            # Cache identifiers from the result
            for entry in entries:
                self._cache_id(
                    os.path.join(current_path, Client.quote(entry["fileName"])),
                    entry["id"],
                )

        # Cache file information
        for entry in entries:
            self._id_to_stat[int(entry["id"])] = {
                key: entry[key]
                for key in ("id", "size", "md5", "createTime", "updateTime")
            }

        return entries

    def stat_path(self, path):
        """
        Get metadata for the filename at path.
        """

        ident = self._path_to_id[path]
        return self.stat_id(ident)

    def stat_id(self, ident):
        """
        Get metadata for the file with the given identifier ident.
        """

        return self._id_to_stat[int(ident)]

    def upload_file_path(self, src, dstpath):
        """
        Upload the file named src to the folder at path dstpath.
        """

        try:
            dstident = self._path_to_id[dstpath]
        except KeyError:
            raise RuntimeError(
                "Destination path not previously seen, use identifer instead"
            )

        return self.upload_file_id(self, src, ident=dstident)

    def upload_file_id(self, src, ident=0):
        """
        Upload the file named src to the folder with identifier ident.
        """

        return supernote.upload_file(self._token, src, directory=dstident)

    def download_file_path(self, path, filename):
        """
        Download the file named path to the local file named filename.
        """

        ident = self._path_to_id[path]
        return self.download_file_id(ident, filename)

    def download_file_id(self, ident, filename):
        """
        Download the file with identifier ident to the local file named filename.
        """

        return supernote.download_file(self._token, ident, filename)

    def walk_path(self, path=""):
        """
        Walk the folder tree. If path is given, start at the named
        path. Otherwise start at the top.

        This behaves similarly to os.path.walk(path).
        """

        try:
            ident = self._path_to_id[path]
        except KeyError:
            raise RuntimeError("Path not previously seen, use identifier instead")

        return self.walk_id(self, ident=ident)

    def walk_id(self, ident=0):
        """
        Walk the folder tree. If an identifier is given, start at the folder
        with that identifier. Otherwise start at the top.
        """

        # List what's in a folder
        entries = self._file_list(ident=ident)

        # Separate folders from files
        folders = []
        files = []
        current_path = self._id_to_path[int(ident)]
        for entry in entries:
            if entry["isFolder"] == "Y":
                folders.append(entry)
            else:
                files.append(entry)

        foldernames = [Client.quote(folder["fileName"]) for folder in folders]
        yield (
            current_path,
            foldernames,
            [Client.quote(file["fileName"]) for file in files],
        )

        # Trim folders in case foldernames was modified by caller
        folders = [
            folder
            for folder in folders
            if Client.quote(folder["fileName"]) in foldernames
        ]
        for folder in folders:
            yield from self.walk_id(ident=folder["id"])

    def walk(self):
        """
        Walk the folder tree from the top.
        """

        return self.walk_id()
