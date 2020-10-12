from gmail import Gmail
from fuse import FUSE, FuseOSError, Operations
import stat
from time import time
from errno import ENOENT


'''
Todo: 
1. use labelId to filter inbox and sent

'''

class GmailFS(Operations):
    def __init__(self):
        self.gmail_client = Gmail()

    def getattr(self, path, fh=None):
        st = dict()
        st['st_ctime'] = st['st_mtime'] = st['st_atime'] = time()
        if path == '/' or path == '/inbox':
            st['st_mode'] = stat.S_IFDIR | 0o774
        elif '/inbox/' in path:
            subject = path.split('/inbox/')[1]
            st['st_mode'] = stat.S_IFREG | 0o444
            st['st_size'] = self.metadata_dict[subject]['size']
            st['st_ctime'] = st['st_mtime'] = st['st_atime'] = self.metadata_dict[subject]['date']
            print(path)
        else:
            raise FuseOSError(ENOENT)
        
        return st

    def readdir(self, path, fh):
        if path == '/':
            return ['.', '..', 'inbox']
        if path == '/inbox':
            self.metadata_dict, subject_list = self.gmail_client.get_email_list()
            return ['.', '..'] + subject_list

    # Disable unused operations:
    access = None
    flush = None
    getxattr = None
    listxattr = None
    open = None
    opendir = None
    release = None
    releasedir = None
    statfs = None

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('mount')
    args = parser.parse_args()

    fuse = FUSE(GmailFS(), args.mount, foreground=True, ro=True)