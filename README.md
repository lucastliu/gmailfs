# gmailfs
filesystem based interface to interact with gmail



#### 10.12
```
mkdir client/
python3 ./gmailfs client/
```
- Abstract `Gmail` class to keep the connection (open to discuss...)
    - If go with this design, we can move label, send functions also into this `Gmail` class

Below is the current status of *inbox*
- `readdir` - request a list of emails in metadata format: keep a `metadata_dict` for `getattr` usage 

Todo: 
- Bug
[] Handle emails of duplicate subject line (stuck..for now just keep one...unacceptable)
[] Email subject as filenames has quotation marks, need to remove(should be easy to figure out...but i stuck again)

- Next step
[] support `cat`: request message in MIME, display full text in parts