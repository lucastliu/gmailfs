from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import gmail_func.send_email
import email_draft_parse
import googleapiclient.errors as google_error
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase

import base64
import email

# based on implementation from https://blog.mailtrap.io/send-emails-with-gmail-api/#Step_9_Read_a_specific_email_from_your_inbox

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://mail.google.com/']


class Gmail():
    def __init__(self):
        """
        Shows basic usage of the Gmail API.
        Lists the user's Gmail labels.
        """
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('gmail', 'v1', credentials=creds)
        self.user_id = "me"

    ### util functions
    def get_messages(self, label=None):
        service, user_id = self.service, self.user_id
        try:
            return service.users().messages().list(userId=user_id, labelIds=label).execute()
        except Exception as error:
            print('An error occurred: %s' % error)

    def get_meta_message(self, msg_id):
        service, user_id = self.service, self.user_id
        try:
            return service.users().messages().get(userId=user_id, id=msg_id, format='metadata').execute()
        except Exception as error:
            print('An error occurred: %s' % error)

    def get_mime_message(self, msg_id):
        service, user_id = self.service, self.user_id
        try:
            message = service.users().messages().get(userId=user_id, id=msg_id,
                                                     format='raw').execute()
            print('Message snippet: %s' % message['snippet'])
            msg_str = base64.urlsafe_b64decode(
                message['raw'].encode("utf-8")).decode("utf-8")
            mime_msg = email.message_from_string(msg_str)

            return mime_msg
        except Exception as error:
            print('An error occurred: %s' % error)

    def get_attachments(self, msg_id, store_dir):
        service, user_id = self.service, self.user_id
        try:
            message = service.users().messages().get(userId=user_id, id=msg_id).execute()

            for part in message['payload']['parts']:
                if (part['filename'] and part['body'] and part['body']['attachmentId']):
                    attachment = service.users().messages().attachments().get(
                        id=part['body']['attachmentId'], userId=user_id, messageId=msg_id).execute()

                    file_data = base64.urlsafe_b64decode(
                        attachment['data'].encode('utf-8'))
                    path = ''.join([store_dir, part['filename']])

                    f = open(path, 'wb')
                    f.write(file_data)
                    f.close()
        except Exception as error:
            print('An error occurred: %s' % error)

    ### combination functions
    def get_email_list(self):
        # https://developers.google.com/gmail/api/reference/rest/v1/users.messages/list
        # for now just return all
        messages = self.get_messages('INBOX')['messages']
        subject_list = []
        metadata_dict = {}

        # iterate each id in messages list, get meta
        for m in messages:

            # request specific message in meta by id
            m_meta = self.get_meta_message(m['id'])

            meta = {}
            subject = ''
            for header in m_meta['payload']['headers']:
                if header['name'] == 'Subject':
                    subject = header['value']
                    break

            # for stat
            meta['date'] = int(m_meta['internalDate']) / 1000 #gmail's timestamp is in millisecond, so divide by 1000
            meta['size'] = int(m_meta['sizeEstimate'])

            # unique identifier, for fetch full text
            meta['id'] = m_meta['id']

            key = subject + " ID " + m_meta['id']
            metadata_dict[key] = meta
            subject_list.append(key)

        return metadata_dict, subject_list
        # message = get_mime_message(service, user_id, messages['messages'][1]['id'])

    def send_email(self, draft):
        vals = email_draft_parse.extract_fields(draft)
        if len(vals) == 4:
            email_draft = gmail_func.send_email.create_message(*vals)
        else:
            email_draft = gmail_func.send_email.create_message_with_attachment(*vals)
        gmail_func.send_email.send_message(self.service, self.user_id, email_draft)


def test():
    client = Gmail()
    raw = client.get_messages()
    messages = raw['messages']
    email_list = []
    email_mime = []
    for m in messages:
        m_meta = client.get_meta_message(m['id'])
        m_mime = client.get_mime_message(m["id"])
        email_list.append(m_meta)
        email_mime.append(m_mime)
        
    print(email_list)


if __name__ == '__main__':
    test()
