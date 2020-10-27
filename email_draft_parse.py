import re


def extract_field(s, field):
    m = re.search("(^|\n)%s: (.*)\n" % field, s)
    if m:
        return m.group(2)
    return ""


def extract_message(s):
    m = re.search("(^|\n)Message:\n([\S\s]*)", s)
    if m:
        return m.group(2)
    return


def extract_fields(draft):
    fields = ["To", "Subject", "File"]
    vals = ["me"] # The sender is set to me by default, now the user doesn't need to set Sender
    for f in fields:
        val = extract_field(draft, f)
        if val != "":
            vals.append(val)
        else:
            if f == "File":
                continue
            else:
                raise UnspecifiedFieldError("Please specify " + f + "!")
    val = extract_message(draft)
    vals.append(val)
    return vals


class UnspecifiedFieldError(Exception):
    def __init__(self, message):
        super().__init__(message)
