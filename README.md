# gmailfs
filesystem based interface to interact with gmail


## Getting Started:
clone the repository with `git clone git@github.com:lucastliu/gmailfs.git`

Navigate to the repository on your computer `cd gmailfs`


install dependencies
`sudo pip3 --upgrade install -r requirements.txt`
`sudo pip3 install -r requirements.txt`


Make two directories inside gmailfs repository root
```
mkdir client
mkdir cache
```

Run gmailfs `python3 ./gmailfs.py ./cache ./client`

Because currently the gmailfs runs in the foreground, we need to change to another terminal window. After the gmailfs mounts to the ~/client directory, open a new terminal window and again navigate to gmailfs

## Usage

### Read Inbox
View a list of available emails in the inbox
`cd client/inbox`
`ls` 

You should see a list of emails

Read the raw / full MIME content of a specific email
`cat email-subject-plus-email-id`

### Send an Email
First, draft an email by creating a file in the root of the gmailfs repository

Example:
`vim emaildraftname`
start with the structure shown below. Note: You must have a newline after the messages line.

```
Subject: email example
Sender: me
To: whoever.it.is@duke.edu
Message: put-whatever-text-you-want-to-write-here-but-you-cannot-start-a-new-line

```

To send the email, move the email draft to the ~/client/send directory 
`mv emaildraftname ~client/send`
If the email is successfully sent, the email draft in the ~/client/send will be deleted and you can find the sent email in the ~/client/sent directory. 

If the format of the draft is incorrect, the email draft will be deleted, and no action will be taken.

To check the email you just sent, change to the ~/client/sent directory
`cd /client/sent`
`ls`

### Close gmailfs
To stop the program, press ctrl-c in the terminal window which runs `python3 ./gmailfs.py ~/cache ~/client`

After program termination, you can still view the contents under the ~/cache folder, but the contents will not update anymore.


## References:
1. python fuse sample: https://github.com/skorokithakis/python-fuse-sample
