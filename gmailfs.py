from gmail import Gmail
from fuse import FUSE, FuseOSError, Operations
import stat
from time import time
import errno
from enum import Enum
from lru import LRUCache
import threading
import os
import shutil
import sys
import re

# from multiprocessing import Process, Lock

import time as TT
import subprocess


# Reference: the basic code in this file is adopted from this python fuse
# sample: https://github.com/skorokithakis/python-fuse-sample


class GmailFS(Operations):
    def __init__(self, root, lru_capacity):
        # self.lock = Lock()
        self.gmail_client = Gmail()
        self.metadata_dict, _, self.subject_by_id = self.gmail_client.get_email_list()
        self.root = root
        self.client = os.path.basename(root)
        self.eid_by_path = dict()
        self.lru = LRUCache(lru_capacity, self)
        self.lru_capacity = lru_capacity
        self.gmail_client.gmailfs = self

    def __enter__(self):
        print("start...")
        self.inbox_cache_directory = self._full_path("/inbox/")
        send_directory = self._full_path("/send/")
        sent_directory = self._full_path("/sent/")

        for directory in [self.inbox_cache_directory, send_directory, sent_directory]:
            if not os.path.exists(directory):
                os.makedirs(directory)
        self.metadata_dict, subject_list, _ = self.gmail_client.get_email_list()

        cache_subject_list = subject_list[:self.lru_capacity] if self.lru_capacity < len(subject_list) else subject_list
        cache_subject_list.reverse()  # add to cache from old to new
        for email_subject_line in cache_subject_list:
            if len(self.lru) >= self.lru_capacity:
                break

            email_id = self.metadata_dict[email_subject_line]["id"]
            self.lru.add_new_email(email_id, email_subject_line)
            # mime = self.gmail_client.get_mime_message(email_id)
            # relative_folder_path = "/inbox/" + email_subject_line
            # folder_path = self._full_path(relative_folder_path)
            # if not os.path.exists(folder_path):
            #     os.makedirs(folder_path)
            # raw_path = self._full_path(relative_folder_path + "/raw")
            # with open(raw_path, "w+") as f:
            #     f.write(str(mime))
            # self.lru.add(folder_path)
        return self

    def __exit__(self, type, value, traceback):
        shutil.rmtree(self.inbox_cache_directory)
        print("exit...")
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
        m = re.search(rf"^.*\/{self.client}\/inbox\/.*?([^\\]\/|$)", full_path)
        if m:
            inbox_folder_path = m.group(0)
            if not os.path.exists(inbox_folder_path):
                os.makedirs(inbox_folder_path)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        print("chmod")
        full_path = self._full_path(path)
        return os.chmod(full_path, mode)

    def chown(self, path, uid, gid):
        print("chown")
        full_path = self._full_path(path)
        return os.chown(full_path, uid, gid)

    class PATH_TYPE(Enum):
        EMAIL_FOLDER = 1
        EMAIL_CONTENT = 2

    def path_type(self, path):
        if '/inbox/' not in path:
            return False
        path_tuple = path.split('/')
        if len(path_tuple) == 3:
            return GmailFS.PATH_TYPE.EMAIL_FOLDER
        if len(path_tuple) == 4:
            return GmailFS.PATH_TYPE.EMAIL_CONTENT

    def getattr(self, path, fh=None):
        st = dict()
        if path == '/' or path == '/inbox':
            st['st_mode'] = stat.S_IFDIR | 0o774
        # attr for each email folder e.g. 
        # ['', 'inbox', 'Basic Email Test ID 17519d916b1681af']
        elif self.path_type(path) == GmailFS.PATH_TYPE.EMAIL_FOLDER:
            subject = path.split('/inbox/')[1]
            if subject not in self.metadata_dict:
                return st
            st['st_ctime'] = st['st_mtime'] = st['st_atime'] = time()
            st['st_mode'] = stat.S_IFDIR | 0o774
            st['st_size'] = self.metadata_dict[subject]['size']
            st['st_ctime'] = st['st_mtime'] = st['st_atime'] = self.metadata_dict[subject]['date']
            # create empty folder for each email in cache folder
            # TODO: can I remove this?
            # if not os.path.isdir(self._full_path(path)):
            #     full_path = self._full_path(path)
            #     os.makedirs(full_path)
        # attr for raw, html, plainTxt in email folder
        elif self.path_type(path) == GmailFS.PATH_TYPE.EMAIL_CONTENT:
            subject = path.split('/')[2]
            if subject not in self.metadata_dict:
                return st
            st['st_ctime'] = st['st_mtime'] = st['st_atime'] = time()
            st['st_mode'] = stat.S_IFREG | 0o444
            st['st_size'] = self.metadata_dict[subject]['size']
            st['st_ctime'] = st['st_mtime'] = st['st_atime'] = self.metadata_dict[subject]['date']
        # if we want to see the normal files in the cache folder
        else:
            full_path = self._full_path(path)
            st = os.lstat(full_path)
            return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                                                            'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size',
                                                            'st_uid'))
        return st

    def readdir(self, path, fh):
        if path == '/inbox':
            self.metadata_dict, subject_list, _ = self.gmail_client.get_email_list()
            return ['.', '..'] + subject_list
        elif self.path_type(path) == GmailFS.PATH_TYPE.EMAIL_FOLDER:
            return ['.', '..', 'raw', 'html', 'plaintxt']
        else:
            dirents = ['.', '..']
            full_path = self._full_path(path)
            # if we want to see the normal files in the cache folder
            if os.path.isdir(full_path):
                existing_file_list = os.listdir(full_path)
                filter(lambda s: s == "inbox", existing_file_list)
                dirents.extend(os.listdir(full_path))
            return dirents

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

        inbox_folder_path = None
        m = re.search(rf"(^.*\/{self.client}\/inbox\/.*?[^\\])\/", full_path)
        if m:
            inbox_folder_path = m.group(1)

        if inbox_folder_path:
            if os.path.exists(full_path):
                # update the entry order in lru
                self.lru.move_to_end(inbox_folder_path)
            else:

                # add to lru and delete the oldest entry
                self.lru.add(inbox_folder_path)

                if not os.path.exists(inbox_folder_path):
                    os.makedirs(inbox_folder_path)

                # mapping fake address
                path_tuple = full_path.split('/')
                raw_path = '/'.join(path_tuple[:-1]) + '/raw'
                # fetch MIME type email as base
                if os.path.basename(full_path) == 'raw' or not os.path.exists(raw_path):
                    email_subject_line = path_tuple[-2]
                    email_id = self.metadata_dict[email_subject_line]["id"]
                    mime = self.gmail_client.get_mime_message(email_id)
                    with open(raw_path, "w+") as f:
                        f.write(str(mime))
                if os.path.basename(full_path) == 'html':
                    with open(raw_path, "r") as f, open(full_path, "a+") as f_html:
                        lines_list = f.readlines()
                        is_html = False
                        for line in lines_list[1:]:
                            if is_html:
                                if line.find('</html>') != -1:
                                    index = line.find('</html>')
                                    print(line)
                                    f_html.write(line[:index + len('</html>')])
                                    break
                                else:
                                    f_html.write(line)
                            elif not is_html and line.find('<html') != -1:
                                index = line.find('<html')
                                f_html.write(line[index:])
                                is_html = True

        fd = os.open(full_path, flags)

        return fd

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
        try:
            if path.startswith("/send"):
                send_path = self._full_path(path)
                sent_path = send_path.replace("/send", "/sent", 1)
                with open(send_path, "r") as f:
                    draft = f.read()
                    self.gmail_client.send_email(draft)
                os.rename(send_path, sent_path)
                print("Success: email sent")
        except Exception as send_err:
            send_directory = self._full_path("/send/")
            for f in os.listdir(send_directory):
                f_path = os.path.join(send_directory, f)
                try:
                    if os.path.isfile(f_path) or os.path.islink(f_path):
                        os.unlink(f_path)
                    elif os.path.isdir(f_path):
                        shutil.rmtree(f_path)
                except Exception as delete_err:
                    print(
                        "Error: could not empty send folder, reason: " + str(delete_err))
            print("Error: " + str(send_err))
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        print("fsync")
        return self.flush(path, fh)


def func1(lock):
    """
    Example function that uses a lock
    """
    print('func1: starting')
    for i in range(10000):
        if i % 1000 == 0:
            lock.acquire()
            print("STUFF")
            lock.release()
    print('func1: finishing')


if __name__ == '__main__':

    if not os.path.exists("./client"):
        os.makedirs("./client")
    if not os.path.exists("./src"):
        os.makedirs("./src")
    try:
        with GmailFS("./src", 10) as G:
            kwa = {'nothreads': True, 'foreground': True}
            t1 = threading.Thread(target=FUSE, args=(G, "./client"), kwargs=kwa)
            t1.daemon = True
            t2 = threading.Thread(target=G.gmail_client.listen_for_updates)
            t2.daemon = True
            t1.start()
            t2.start()
            while t1.is_alive() or t2.is_alive():
                TT.sleep(1)

    except KeyboardInterrupt:
        print("Force Close")
        t1.join(1)
        t2.join(1)
        process = subprocess.Popen(['umount', 'client'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.communicate()
        sys.exit(0)




    # lock = Lock()
    # with GmailFS(sys.argv[1], 10) as G:
    #     kwa = {'nothreads': True, 'foreground': True}
    #     p1 = Process(target=FUSE, args=(G, sys.argv[2]), kwargs=kwa)
    #     p1.daemon = True
    #     p2 = Process(target=G.gmail_client.listen_for_updates, args=(lock,))
    #     p2.daemon = True
    #
    #     p1.start()
    #     p2.start()
    #
    #     try:
    #         p1.join()
    #         p2.join()
    #     except KeyboardInterrupt:
    #         p1.terminate()
    #         p1.join()
    #         p2.terminate()
    #         p2.join()

    # FUSE(GmailFS(sys.argv[1]), sys.argv[2], nothreads=True, foreground=True)
