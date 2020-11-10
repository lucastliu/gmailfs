from __future__ import print_function
import pickle
import os.path

import googleapiclient
from googleapiclient import _auth
import sys
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

from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from multiprocessing import Lock

import ast

import os

import configparser

import time
import traceback



os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "project_key.json"

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
        self.creds = creds
        self.http = googleapiclient._auth.authorized_http(self.creds)

        self.config = configparser.ConfigParser()
        self.config.sections()
        self.config.read('config.ini')
        self.historyId = 0
        self.gmailfs = None
        self.subname = self.config['GMAIL']['subname']
        self.topic = self.config['GMAIL']['topic']
        self.projectID = self.config['GMAIL']['projectid']

        self.start_autoupdate_service()

    ### util functions
    def get_messages(self, label=None):
        service, user_id = self.service, self.user_id
        try:
            return service.users().messages().list(userId=user_id, labelIds=label).execute(_auth.authorized_http(self.creds))
        except Exception as error:
            print('An error occurred: %s' % error)

    def get_meta_message(self, msg_id):
        service, user_id = self.service, self.user_id
        try:
            return service.users().messages().get(userId=user_id, id=msg_id, format='metadata').execute(_auth.authorized_http(self.creds))
        except Exception as error:
            print('An error occurred during get meta message: %s' % error)

    def get_mime_message(self, msg_id):
        service, user_id = self.service, self.user_id
        try:
            message = service.users().messages().get(userId=user_id, id=msg_id,
                                                     format='raw').execute(_auth.authorized_http(self.creds))
            if message is None:
                raise NonexistenceEmailError(f"Email {msg_id} doesn't exist")
            print('Message snippet: %s' % message['snippet'])
            msg_str = base64.urlsafe_b64decode(
                message['raw'].encode("utf-8")).decode("utf-8")
            mime_msg = email.message_from_string(msg_str)
            if mime_msg.is_multipart():
                for part in mime_msg.walk():
                    if part.get_content_type() == 'text/plain' or  part.get_content_type() == 'text/html':
                        part.set_payload(part.get_payload(decode=True).decode('utf-8'))
                    if part.get_content_disposition():
                        part.set_payload("Please find attachment in the email folder.")
            return mime_msg
        except googleapiclient.errors.HttpError as http_error:
            raise NonexistenceEmailError(f"Email {msg_id} doesn't exist")
        except Exception as error:
            print('An error occurred: %s' % error)

    def get_attachments(self, msg_id, store_dir):
        service, user_id = self.service, self.user_id
        # try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute(_auth.authorized_http(self.creds))
        if message is None or 'parts' not in message['payload']:
            return
            # raise NonexistenceEmailError("Email attachments don't exist")
        for part in message['payload']['parts']:
            if (part['filename'] and part['body'] and part['body']['attachmentId']):
                attachment = service.users().messages().attachments().get(
                    id=part['body']['attachmentId'], userId=user_id, messageId=msg_id).execute(_auth.authorized_http(self.creds))

                file_data = base64.urlsafe_b64decode(
                    attachment['data'].encode('utf-8'))
                path = ''.join([store_dir, part['filename']])

                f = open(path, 'wb')
                f.write(file_data)
                f.close()
        # except TypeError as error:
        #     print('An error occurred: %s' % error)

    def get_subject_and_metadata_with_id(self, email_id):
        m_meta = self.get_meta_message(email_id)
        # TODO: historyId
        # You can get each messages' historyId like this:
        # print(m_meta['historyId'])
        # the first message m's historyId will be the most recent.
        # Messages are ordered from most recent to oldest
        meta = {}
        subject = ''
        for header in m_meta['payload']['headers']:
            if header['name'] == 'Subject':
                subject = header['value']
                break

        # for stat
        meta['date'] = int(m_meta['internalDate']) / 1000  # gmail's timestamp is in millisecond, so divide by 1000
        meta['size'] = int(m_meta['sizeEstimate'])

        # unique identifier, for fetch full text
        meta['id'] = m_meta['id']

        return subject, meta

    ### combination functions
    def get_email_list(self):
        # https://developers.google.com/gmail/api/reference/rest/v1/users.messages/list
        # for now just return all
        messages = self.get_messages('INBOX')['messages']
        subject_list = []
        metadata_dict = {}
        subject_by_id = {}

        # iterate each id in messages list, get meta
        for m in messages:

            # # request specific message in meta by id
            # m_meta = self.get_meta_message(m['id'])
            # # TODO: historyId
            # # You can get each messages' historyId like this:
            # # print(m_meta['historyId'])
            # # the first message m's historyId will be the most recent.
            # # Messages are ordered from most recent to oldest
            # meta = {}
            # subject = ''
            # for header in m_meta['payload']['headers']:
            #     if header['name'] == 'Subject':
            #         subject = header['value']
            #         break
            #
            # # for stat
            # meta['date'] = int(m_meta['internalDate']) / 1000 #gmail's timestamp is in millisecond, so divide by 1000
            # meta['size'] = int(m_meta['sizeEstimate'])
            #
            # # unique identifier, for fetch full text
            # meta['id'] = m_meta['id']
            #
            subject, meta = self.get_subject_and_metadata_with_id(m['id'])
            key = subject + " ID " + meta['id']
            metadata_dict[key] = meta
            subject_by_id[meta['id']] = key
            subject_list.append(key)

        return metadata_dict, subject_list, subject_by_id
        # message = get_mime_message(service, user_id, messages['messages'][1]['id'])

    def send_email(self, draft):
        vals = email_draft_parse.extract_fields(draft)
        if len(vals) == 4:
            email_draft = gmail_func.send_email.create_message(*vals)
        else:
            email_draft = gmail_func.send_email.create_message_with_attachment(*vals)
        gmail_func.send_email.send_message(self.service, self.user_id, email_draft)

    def start_autoupdate_service(self):
        request = {
            'labelIds': ['INBOX'],
            'topicName': self.topic
        }

        response = self.service.users().watch(userId='me', body=request).execute(_auth.authorized_http(self.creds))
        self.historyId = response['historyId']
        print('Starting History ID: {}'.format(self.historyId))

    def partial_sync(self, startHistoryId=None):
        # notifies of all changes after given historyId
        if(startHistoryId is None):
            startHistoryId = self.historyId

        def parse(history, changetype, function):
            """
            history: Google API history object
            changetype: history changetype requested
            function: function that all relevant message objects should be passed to
            """
            if changetype in history:
                print(str(changetype))
                for msg in history[changetype]:
                    print(msg['message']['id'])
                    function(msg)

        def lru_add(msg):
            if('INBOX' in msg['message']['labelIds']):
                print('added to inbox')
                self.gmailfs.lru.add_new_email(msg['message']['id'])

        def lru_remove(msg):
            if('INBOX' in msg['message']['labelIds']):
                print('removed from inbox')
                self.gmailfs.lru.delete_message(msg['message']['id'])

        def isMovetoInbox(msg):
            if('INBOX' in msg['labelIds']):
                print('added to inbox')
                self.gmailfs.lru.add_new_email(msg['message']['id'])

        def isRemoveFromInbox(msg):
            if('INBOX' in msg['labelIds']):
                print('removed from inbox')
                self.gmailfs.lru.delete_message(msg['message']['id'])
        try:
            histories = self.service.users().history()\
                     .list(userId='me',
                           startHistoryId=startHistoryId).execute(_auth.authorized_http(self.creds))
            if(histories and 'history' in histories):
                histories = histories['history']
                for history in histories:
                    #print("NH ------------------------")
                    #print(history)
                    parse(history, 'messagesAdded', lru_add)
                    parse(history, 'messagesDeleted', lru_remove)
                    parse(history, 'labelsAdded', isMovetoInbox)
                    parse(history, 'labelsRemoved', isRemoveFromInbox)

        except Exception as error:
            print('An error occurred during autoupdate: %s' % error)
            print(traceback.print_exc())

    def listen_for_updates(self):
        project_id = self.projectID
        subscription_id = self.subname
        subscriber = pubsub_v1.SubscriberClient()
        # The `subscription_path` method creates a fully qualified identifier
        # in the form `projects/{project_id}/subscriptions/{subscription_id}`
        subscription_path = subscriber.subscription_path(project_id,
                                                         subscription_id)

        def callback(message):
            # lock.acquire()
            #print(f"Received {message}.")
            data = ast.literal_eval(message.data.decode("utf-8"))
            print('---------- New Update: {} ---------- '.format(data['historyId']))
            self.partial_sync()
            self.historyId = data['historyId']
            message.ack()
            # lock.release()

        streaming_pull_future = subscriber.subscribe(subscription_path,
                                                     callback=callback)
        print(f"Listening for messages on {subscription_path}..\n")

        # Wrap subscriber in a 'with' block to automatically call close() when done.
        with subscriber:
            try:
                # When `timeout` is not set, result() will block indefinitely,
                # unless an exception is encountered first.
                streaming_pull_future.result()
            except TimeoutError:
                streaming_pull_future.cancel()


def test():
    client = Gmail()
    # lock = Lock()
    # client.listen_for_updates(lock)
    raw = client.get_messages()
    messages = raw['messages']
    email_list = []
    email_mime = []
    for m in messages:
        if m['id'] == '17519a4cd78744f9':
            # m_meta = client.get_meta_message(m['id'])
            m_mime = client.get_mime_message(m["id"])
            # email_list.append(m_meta)
            email_mime.append(m_mime)
            print(m_mime)

    # print(email_mime)


if __name__ == '__main__':
    test()


class NonexistenceEmailError(Exception):
    def __init__(self, message):
        super().__init__(message)