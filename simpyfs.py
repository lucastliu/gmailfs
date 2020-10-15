#!/usr/bin/env python

from __future__ import with_statement

import os
import sys
import errno
import stat
from time import time
from errno import ENOENT
from fuse import FUSE, FuseOSError, Operations

from gmail import Gmail

mock_emails = [
    {
        "id": "mockid",
        "threadId": "mock-thread-id",
        "labelIds": [
            "mock-lable-id-1", "mock-lable-id-2"
        ],
        "snippet": "Duke will be conducting ongoing surveillance testing of students and other members of the campus community who are not exhibiting any symptoms of COVID-19.",
        "historyId": "mock-history-id",
        "internalDate": "mock-internal-data",
        "payload": {},
        "sizeEstimate": 2000,
        "raw":
            """
  Duke will be conducting ongoing surveillance testing of students and other members of the campus community who are not exhibiting any symptoms of COVID-19. This is a critical part of helping us identify and respond to the asymptomatic spread of the virus and limit the potential for local outbreaks.
You are scheduled for a surveillance test tomorrow. This test is required, even if you recently completed a COVID-19 test.Surveillance testing may require you to take more than one test per week during the semester.
Please visit any of the many locations on East or West campus to complete this test, which should take no more than 5 minutes.
You will only be contacted afterward if you test positive, at which point you will receive further medical guidance and support.
You can find more information about the process, testing locations and answers to frequently asked questions on the Duke United website. IF YOU HAVE NOT TESTED BEFORE, please watch the brief video that describes the testing process before you arrive to save you time.
Undergraduates with questions should email keeplearning@duke.edu, and graduate/professional students should email the appropriate program contact for their respective school.
This message was sent by Duke United Testing via Duke Notify. To change your delivery preferences, please visit Duke Notify.
            """
    }]


class Passthrough(Operations):
    def __init__(self, root):
        self.gmail_client = Gmail()
        self.root = root

    # Helpers
    # =======

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        print("access")
        full_path = self._full_path(path)
        # if not os.access(full_path, mode):
        #     raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        print("chmod")
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        print("chown")
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    def getattr(self, path, fh=None):
        print("getattr")
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                                                        'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size',
                                                        'st_uid'))

    def readdir(self, path, fh):
        print("readdir")

        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def readlink(self, path):
        print("readlink")
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        print("mknod")

        return os.mknod(self._full_path(path), mode, dev)

    def rmdir(self, path):
        print("rmdir")

        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def mkdir(self, path, mode):
        print("mkdir")

        return os.mkdir(self._full_path(path), mode)

    def statfs(self, path):
        print("statfs")
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
                                                         'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files',
                                                         'f_flag',
                                                         'f_frsize', 'f_namemax'))

    def unlink(self, path):
        print("unlink")

        return os.unlink(self._full_path(path))

    def symlink(self, name, target):
        return os.symlink(target, self._full_path(name))

    def rename(self, old, new):
        print("rename")

        return os.rename(self._full_path(old), self._full_path(new))

    def link(self, target, name):
        return os.link(self._full_path(name), self._full_path(target))

    def utimens(self, path, times=None):
        print("utimens")

        return os.utime(self._full_path(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        print("open")

        full_path = self._full_path(path)
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        print("create")

        full_path = self._full_path(path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def read(self, path, length, offset, fh):
        print("read")

        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        print("write")

        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        print("truncate")

        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        print("flush")

        return os.fsync(fh)

    def release(self, path, fh):
        print("release")

        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        print("fsync")

        return self.flush(path, fh)


# def data_init(root):
#     for email in mock_emails:
#         with open(os.path.join(root, email["id"] + ".html"), "w+") as f:
#             f.write(email["raw"])


def main(mountpoint, root):
    # data_init(root)
    FUSE(Passthrough(root), mountpoint, nothreads=True, foreground=True)


if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])
