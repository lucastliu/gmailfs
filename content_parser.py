import os
import email

class Parser:
    def __init__(self, raw_path, email_folder_name):
        # parsed file directory
        self.boundary = None
        self.raw_path = raw_path
        self.email_folder_name = email_folder_name
        self.type = []
        with open(raw_path, "r") as f:
            # Content-Type
            finished = False
            while not finished:
                line = f.readline()
                if not line:
                    finished = True
                if 'Content-Type: ' in line:
                    if 'html' in line:
                        self.type.append('html')
                    if 'plain' in line:
                        self.type.append('plain')

    def update_boundary(self, line):
        if "boundary=" in line:
            start = line.find('boundary="') + len('boundary="') + 1
            end = line[start:].find('"')
            # print(line[start:start + end])
            self.boundary = line[start:start + end]

    # file_type = 'html' or 'plain'
    def get_str(self, file_type):
        offset = 0
        length = 0
        if file_type in self.type:
            # need to parse now!
            with open(self.raw_path, "r") as f:
                finished = False
                while not finished:
                    line = f.readline()
                    self.update_boundary(line)
                    if 'Content-Type: text/' + file_type + ';' in line:
                        is_content = False
                        self.update_boundary(line)
                        while not finished:
                            #    Needed part start
                            if not is_content and '\n' == line:
                                is_content = True
                                offset += len(line)
                            #     doesn't reach to the end
                            elif is_content and line and (not self.boundary or (self.boundary and not self.boundary in line)):
                                length += len(line)
                            #     End of the needed part
                            elif not line or (self.boundary and self.boundary in line):
                                finished = True
                                break
                            else:
                                offset += len(line)
                            line = f.readline()
                    else:
                        offset += len(line)
        return offset, length

def test():
    p = Parser("finish.txt", "BASIC_EMAIL ID 1234")
    offset, length = p.get_str('plain')
    with open(p.raw_path, "r") as f:
        f.seek(offset)
        parsed = f.read(length)
    print("------------------------")
    print(offset, length)
    print(parsed)
    return


if __name__ == '__main__':
    test()