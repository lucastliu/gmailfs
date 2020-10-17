import re


def extract_field(s, field):
    m = re.search("(^|\n)%s: (.*)\n" % field, s)
    if m:
        return m.group(2)
    return ""


def extract_fields(draft):
    fields = ["Sender", "To", "Subject", "Message", "File"]
    vals = []
    for f in fields:
        val = extract_field(draft, f)
        if val != "":
            vals.append(val)
        else:
            if f == "File":
                continue
            else:
                raise UnspecifiedFieldError("Please specify " + f + "!")

    return vals


class UnspecifiedFieldError(Exception):
    def __init__(self, message):
        super().__init__(message)
