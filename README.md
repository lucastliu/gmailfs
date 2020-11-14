# gmailfs
filesystem based interface to interact with gmail



## Getting Started:

Note: intended for Linux distributions. Tested on Ubuntu 20.04

clone the repository with `git clone git@github.com:lucastliu/gmailfs.git`

Navigate to the repository on your computer `cd gmailfs`

install dependencies
`sudo pip3 --upgrade install -r requirements.txt`

`sudo pip3 install -r requirements.txt`


### Google Account Pre-requisite Steps

Various credential details will need to be noted and later added to a configuration file throughout this process.

[Create a Google account](https://accounts.google.com/signup/v2/webcreateaccount?hl=en&flowName=GlifWebSignIn&flowEntry=SignUp), which will give you a gmail email address to use.

Now we must give gmail permission to enable the API with our account.

Complete Step 1 in this [tutorial](https://developers.google.com/gmail/api/quickstart/js) to create a new project and enable the Gmail API. Take note of the project name and ID.

The [Google cloud console](https://console.cloud.google.com) is your place to add and modify features which will allow gmailfs to auto-update with your email contents.

Complete the first portion of this guide, [Initial Cloud Pub/Sub Setup](https://developers.google.com/gmail/api/guides/push). Note the topic name and ID.

Create a service account with a Pub/Sub Admin role under the `Credentials` section of the `APIs & Services` in Google Cloud console. Generate a key for this service account. Download the json credentials, saving the file as `project_key.json` in the root directory of the gmailfs project.

In the same section, create a new OAuth client ID for a `Desktop Application`. Download the credentials, saving it as `credentials.json`, and place file into the root of the gmailfs project directory.

#### Multiple Instances

If you intend to have multiple instances of gmailfs with the same gmail account, you will need to complete the steps in this section for each new instance.

Create a new pull subscription to the topic established above for gmail updates. Note the name of the subscription.


##### Create the Configuration File

Within the project root, create a new file named `config.ini`
Fill the contents according to this template, replacing the your fields with your information:

```
[GMAIL]
topic = projects/your_project_full_ID_123/topics/your_topic_name
subname = your_subscription_name
projectid = your_project_ID_123
```


### Run gmailfs


Run gmailfs with `python3 ./gmailfs.py`

The first time this program is run, you should be redirected to a browser to authenticate access permissions for this application. You should only need to do this once. A `token.pickle` file will be created for future accesses.

Because gmailfs runs in the foreground, we need to change to another terminal window. Open a new terminal window and again navigate to the gmailfs directory

It may be necessary to run your new terminal as an admin

`sudo -i`

[input your credentials]

## Usage

### Read Inbox
View a list of available emails in the inbox
`cd client/inbox`
`ls` 

You should see a list of directories, and they are named by subject and email id

Read the raw / full MIME content of a specific email
`cd email-subject-plus-email-id`
`cat raw`
`cat html`

### Send an Email
First, draft an email by creating a file in the root of the gmailfs repository

Example:
`vim emaildraftname`
start with the structure shown below. Note: You must have a newline after the messages line.

```
Subject: email example
To: whoever.it.is@duke.edu
File: /absolute/path/to/attachment/
Message:
first line,
second line
third line. 

```

To send the email, move the email draft to the ~/client/send directory 
`mv emaildraftname ~client/send`
If the email is successfully sent, the email draft in the ~/client/send will be deleted and you can find the sent email in the ~/client/sent directory. 

If the format of the draft is incorrect, the email draft will be deleted, and no action will be taken.

To check the email you just sent, change to the ~/client/sent directory
`cd /client/sent`
`ls`

### Delete an Email
To delete an email, cd inbox, rm -r email_folder_name

### Close gmailfs
To stop the program, press ctrl-c one time in the terminal window which ran `python3 ./gmailfs.py`. Wait a few seconds.

After program termination, you can still view the contents under the ~/cache folder, but the contents will not update anymore.


## References:
1. python fuse sample: https://github.com/skorokithakis/python-fuse-sample
