import os
import email

class Parser:
    def __init__(self, raw_path, email_folder_name):
        # parsed file directory
        self.parsed_file_folder = '/tmp/.gmailfs/'
        if not os.path.exists(self.parsed_file_folder):
            os.makedirs(self.parsed_file_folder)
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
                if "boundary=" in line:
                    start = line.find('boundary="') + len('boundary="') + 1
                    end = line[start:].find('"')
                    print(line[start:start + end])
                    self.boundary = line[start:start + end]


    def get_txt(self):
        if 'text' in self.type:
            tmp_file_path = self.parsed_file_folder + self.email_folder_name + '.txt'
            # have been parsed
            if os.path.exists(tmp_file_path):
                return tmp_file_path
            # need to parse now!
            with open(self.raw_path, "r") as f, open(tmp_file_path, "a+") as f_txt:
                # email.message_from_string(a)
                finished = False
                while not finished:
                    line = f.readline()
                    if 'Content-Type: text/plain;' in line:
                        in_txt = False
                        while not finished:
                            line = f.readline()
                            if not in_txt and '\n' == line:
                                in_txt = True
                            elif in_txt and line and not '--_000_' in line:
                                f_txt.write(line)
                            elif '--_000_' in line or not line:
                                finished = True
                                break
                f_txt.write('\n')
            print(tmp_file_path)
            return tmp_file_path
        elif 'html' in self.type:
            # Todo: parse html into plainTXT
            return self.get_html()
        return None

    # file_type = 'html' or 'plain'
    def get_str(self, file_type):
        if file_type in self.type:
            tmp_file_path = self.parsed_file_folder + self.email_folder_name + '.' + file_type
            # have been parsed
            if os.path.exists(tmp_file_path):
                return tmp_file_path
            # need to parse now!
            with open(self.raw_path, "r") as f, open(tmp_file_path, "a+") as f_new:
                finished = False
                self.boundary = None
                while not finished:
                    line = f.readline()
                    if "boundary=" in line:
                        start = line.find('boundary="') + len('boundary="') + 1
                        end = line[start:].find('"')
                        print(line[start:start + end])
                        self.boundary = line[start:start + end]
                    if 'Content-Type: text/' + file_type + ';' in line:
                        is_content = False
                        while not finished:
                            line = f.readline()
                            if not is_content and '\n' == line:
                                is_content = True
                            elif is_content and line and (self.boundary and not self.boundary in line):
                                f_new.write(line)
                            elif self.boundary in line or not line:
                                finished = True
                                break
                f_new.write('\n')
                print(tmp_file_path)
                return tmp_file_path
        return None

def test():
    p = Parser("test_parse_html.txt", "BASIC_EMAIL ID 1234")
    print(p.boundary)
    p.get_str('plain')
    return


if __name__ == '__main__':
    test()