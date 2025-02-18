#!/usr/bin/python
import hashlib
import os
import subprocess
import sys
import SupernoteCloud


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
                        print(f"Up to date: {filename}")
                        continue

            print(f"Downloading: {filename}")
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
        print(f"Configure pass with supernote/{username}")
        sys.exit(1)
    if not stdout:
        print(stderr)
        sys.exit(1)
    password = stdout.splitlines()[0].decode()
    sn = SupernoteCloud.Client(username, password)
    sync(sn, destdir)


if __name__ == "__main__":
    main()
