from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
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


def get_messages(service, user_id):
    try:
        return service.users().messages().list(userId=user_id).execute()
    except Exception as error:
        print('An error occurred: %s' % error)


def get_message(service, user_id, msg_id):
    try:
        return service.users().messages().get(userId=user_id, id=msg_id, format='metadata').execute()
    except Exception as error:
        print('An error occurred: %s' % error)


def get_mime_message(service, user_id, msg_id):
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


def get_attachments(service, user_id, msg_id, store_dir):
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()

        for part in message['payload']['parts']:
            if(part['filename'] and part['body'] and part['body']['attachmentId']):
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


def main():
    """Shows basic usage of the Gmail API.
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
                '../credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    messages = get_messages(service, "me")

    message = get_message(service, "me", messages['messages'][0]['id'])

    print(message)


if __name__ == '__main__':
    main()
