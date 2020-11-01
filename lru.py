from collections import OrderedDict
import shutil
import os
import re


class LRUCache(OrderedDict):

    def __init__(self, capacity, gmailfs):
        super().__init__()
        self.capacity = capacity
        self.gmailfs = gmailfs

    def touch(self, key):
        if key not in self:
            raise ValueError("Touch a nonexistent key")
        self.move_to_end(key)

    def contains(self, key):
        if key not in self:
            return False
        self.move_to_end(key)
        return True

    # return the name of the file which will be kick out of the cache
    def add(self, key):
        if key in self:
            self.move_to_end(key)
        self[key] = None
        if len(self) > self.capacity:
            to_delete = self.popitem(last=False)[0]
            if to_delete:
                shutil.rmtree(to_delete)

    # email_folder_name
    def add_new_email(self, email_id, expected_email_folder_name=None):
        mime = self.gmailfs.gmail_client.get_mime_message(email_id)
        email_folder_name = mime["Subject"] + " ID " + email_id
        if expected_email_folder_name:
            assert expected_email_folder_name == email_folder_name

        relative_folder_path = "/inbox/" + email_folder_name
        folder_path = self.gmailfs._full_path(relative_folder_path)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        raw_path = self.gmailfs._full_path(relative_folder_path + "/raw")
        with open(raw_path, "w+") as f:
            f.write(str(mime))

        self.add(folder_path)

