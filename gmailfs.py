from gmail import Gmailfrom fuse import FUSE, FuseOSError, Operationsimport statfrom time import timeimport errnoimport osimport shutilimport sys# Reference: the basic code in this file is adopted from this python fuse# sample: https://github.com/skorokithakis/python-fuse-sampleclass GmailFS(Operations):    def __init__(self, root):        self.gmail_client = Gmail()        self.metadata_dict, _ = self.gmail_client.get_email_list()        self.root = root        self.eid_by_path = dict()        inbox_cache_directory = self._full_path("/inbox/")        send_directory = self._full_path("/send/")        sent_directory = self._full_path("/sent/")        for directory in [inbox_cache_directory, send_directory, sent_directory]:            if not os.path.exists(directory):                os.makedirs(directory)    # Helpers    # =======    def _full_path(self, partial):        if partial.startswith("/"):            partial = partial[1:]        path = os.path.join(self.root, partial)        return path    # Filesystem methods    # ==================    def access(self, path, mode):        print("access")        full_path = self._full_path(path)        if not os.access(full_path, mode):            raise FuseOSError(errno.EACCES)    def chmod(self, path, mode):        print("chmod")        full_path = self._full_path(path)        return os.chmod(full_path, mode)    def chown(self, path, uid, gid):        print("chown")        full_path = self._full_path(path)        return os.chown(full_path, uid, gid)    def getattr(self, path, fh=None):        st = dict()        if path == '/' or path == '/inbox':            st['st_mode'] = stat.S_IFDIR | 0o774        elif '/inbox/' in path:            subject = path.split('/inbox/')[1]            if subject not in self.metadata_dict:                return st            st['st_ctime'] = st['st_mtime'] = st['st_atime'] = time()            st['st_mode'] = stat.S_IFREG | 0o444            st['st_size'] = self.metadata_dict[subject]['size']            st['st_ctime'] = st['st_mtime'] = st['st_atime'] = self.metadata_dict[subject]['date']        # else:        #     raise FuseOSError(errno.ENOENT)        # if we want to see the normal files in the cache folder        else:            full_path = self._full_path(path)            st = os.lstat(full_path)            return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',                                                            'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size',                                                            'st_uid'))        return st    def readdir(self, path, fh):        if path == '/inbox':            self.metadata_dict, subject_list = self.gmail_client.get_email_list()            return ['.', '..'] + subject_list        else:            dirents = ['.', '..']            full_path = self._full_path(path)            # if we want to see the normal files in the cache folder            if os.path.isdir(full_path):                existing_file_list = os.listdir(full_path)                filter(lambda s: s == "inbox", existing_file_list)                dirents.extend(os.listdir(full_path))            return dirents    def readlink(self, path):        print("readlink")        pathname = os.readlink(self._full_path(path))        if pathname.startswith("/"):            # Path name is absolute, sanitize it.            return os.path.relpath(pathname, self.root)        else:            return pathname    def mknod(self, path, mode, dev):        print("mknod")        return os.mknod(self._full_path(path), mode, dev)    def rmdir(self, path):        print("rmdir")        full_path = self._full_path(path)        return os.rmdir(full_path)    def mkdir(self, path, mode):        print("mkdir")        return os.mkdir(self._full_path(path), mode)    def statfs(self, path):        print("statfs")        full_path = self._full_path(path)        stv = os.statvfs(full_path)        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',                                                         'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files',                                                         'f_flag',                                                         'f_frsize', 'f_namemax'))    def unlink(self, path):        print("unlink")        return os.unlink(self._full_path(path))    def symlink(self, name, target):        return os.symlink(target, self._full_path(name))    def rename(self, old, new):        print("rename")        return os.rename(self._full_path(old), self._full_path(new))    def link(self, target, name):        return os.link(self._full_path(name), self._full_path(target))    def utimens(self, path, times=None):        print("utimens")        return os.utime(self._full_path(path), times)    # File methods    # ============    def open(self, path, flags):        print("open")        full_path = self._full_path(path)        if not os.path.exists(full_path):            email_subject_line = os.path.basename(path)            email_id = self.metadata_dict[email_subject_line]["id"]            mime = self.gmail_client.get_mime_message(email_id)            with open(full_path, "w+") as f:                f.write(str(mime))        fd = os.open(full_path, flags)        return fd    def create(self, path, mode, fi=None):        print("create")        full_path = self._full_path(path)        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)    def read(self, path, length, offset, fh):        print("read")        os.lseek(fh, offset, os.SEEK_SET)        return os.read(fh, length)    def write(self, path, buf, offset, fh):        print("write")        os.lseek(fh, offset, os.SEEK_SET)        return os.write(fh, buf)    def truncate(self, path, length, fh=None):        print("truncate")        full_path = self._full_path(path)        with open(full_path, 'r+') as f:            f.truncate(length)    def flush(self, path, fh):        print("flush")        return os.fsync(fh)    def release(self, path, fh):        print("release")        try:            if path.startswith("/send"):                send_path = self._full_path(path)                sent_path = send_path.replace("/send", "/sent", 1)                with open(send_path, "r") as f:                    draft = f.read()                    self.gmail_client.send_email(draft)                os.rename(send_path, sent_path)                print("Success: email sent")        except Exception as send_err:            send_directory = self._full_path("/send/")            for f in os.listdir(send_directory):                f_path = os.path.join(send_directory, f)                try:                    if os.path.isfile(f_path) or os.path.islink(f_path):                        os.unlink(f_path)                    elif os.path.isdir(f_path):                        shutil.rmtree(f_path)                except Exception as delete_err:                    print("Error: could not empty send folder, reason: " + str(delete_err))            print("Error: " + str(send_err))        return os.close(fh)    def fsync(self, path, fdatasync, fh):        print("fsync")        return self.flush(path, fh)if __name__ == '__main__':    FUSE(GmailFS(sys.argv[1]), sys.argv[2], nothreads=True, foreground=True)