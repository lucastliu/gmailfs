from collections import OrderedDict
import shutil
import os
import threading

from gmail import NonexistenceEmailError
import time

class LRUCache(OrderedDict):

    def __init__(self, capacity, gmailfs):
        super().__init__()
        self.lock = threading.Lock()
        self.capacity = capacity
        self.gmailfs = gmailfs

    def _get_mime_and_folder_name(self, email_id):
        mime = self.gmailfs.gmail_client.get_mime_message(email_id)
        return mime, mime["Subject"] + " ID " + email_id

    def touch(self, key):
        with self.lock:
            if key not in self:
                raise ValueError("Touch a nonexistent key")
            self.move_to_end(key)

    def contains(self, key):
        with self.lock:
            if key not in self:
                return False
            self.move_to_end(key)
            return True

    # return the name of the file which will be kick out of the cache
    def add(self, key):
        to_delete = None
        with self.lock:
            if key in self:
                self.move_to_end(key)
            self[key] = None
            if len(self) > self.capacity:
                to_delete = self.popitem(last=False)[0]
        if to_delete:
            shutil.rmtree(to_delete)

    # email_folder_name
    def add_new_email(self, email_id, expected_email_folder_name=None):
        print("[cache] add an email to lru")
        try:
            mime, email_folder_name = self._get_mime_and_folder_name(email_id)
        except NonexistenceEmailError:
            return

        if expected_email_folder_name:
            assert expected_email_folder_name == email_folder_name

        relative_folder_path = "/inbox/" + email_folder_name
        folder_path = self.gmailfs._full_path(relative_folder_path)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        raw_path = self.gmailfs._full_path(relative_folder_path + "/raw")
        with open(raw_path, "w+") as f:
            self.gmailfs.gmail_client.get_attachments(email_id, self.gmailfs._full_path(relative_folder_path + "/"))
            f.write(str(mime))

        # add to metadata cache
        print("[cache] add an email to metadata cache")
        self.add(folder_path)
        subject, meta = self.gmailfs.gmail_client.get_subject_and_metadata_with_id(email_id)
        now = time.time()
        print("Diff: {} seconds".format(now - meta['date']))

        key = subject + " ID " + meta['id']
        assert key == email_folder_name
        self.gmailfs.metadata_dict[key] = meta

    def delete_message(self, email_id):
        print("[cache] delete an email from lru")
        email_folder_path = os.path.join(self.gmailfs.root, "inbox", self.gmailfs.subject_by_id[email_id])
        if os.path.exists(email_folder_path) and os.path.isdir(email_folder_path):
            del self[email_folder_path]
            shutil.rmtree(email_folder_path)

        # delete from metadata cache
        print("[cache] delete an email from metadata cache")
        del self.gmailfs.metadata_dict[self.gmailfs.subject_by_id[email_id]]

