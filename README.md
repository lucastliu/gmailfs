# gmailfs
filesystem based interface to interact with gmail



#### 10.12
```
mkdir client/
mkdir cache
python3 ./gmailfs cache client/
```
- Abstract `Gmail` class to keep the connection (open to discuss...)
    - If go with this design, we can move label, send functions also into this `Gmail` class

Below is the current status of *inbox*
- `readdir` - request a list of emails in metadata format: keep a `metadata_dict` for `getattr` usage 

Todo: 
- Bug
    - [X] Handle emails of duplicate subject line (stuck..for now just keep one...unacceptable)
    - [X] Email subject as filenames has quotation marks, need to remove(should be easy to figure out...but i stuck again)

- Next step
    - [X] support `cat`: request message in MIME, display full text in parts
    - [ ] support basic sending


#### References:
1. python fuse sample: https://github.com/skorokithakis/python-fuse-sample
