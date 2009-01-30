# -*- Mode: Python; py-indent-offset: 4 -*-
'''Simple module for extracting GNOME style doc comments from C
sources, so I can use them for other purposes.'''

import sys, os, string, re

__all__ = ['extract']

class FunctionDoc:
    def __init__(self):
        self.name = None
        self.params = []
        self.description = ''
        self.ret = ''
    def set_name(self, name):
        self.name = name
    def add_param(self, name, description):
        if name == '...':
            name = 'Varargs'
        self.params.append((name, description))
    def append_to_last_param(self, extra):
        self.params[-1] = (self.params[-1][0], self.params[-1][1] + extra)
    def append_to_named_param(self, name, extra):
        for i in range(len(self.params)):
            if self.params[i][0] == name:
                self.params[i] = (name, self.params[i][1] + extra)
                return
        # fall through to adding extra parameter ...
        self.add_param(name, extra)
    def append_description(self, extra):
        self.description = self.description + extra
    def append_return(self, extra):
        self.ret = self.ret + extra

    def get_param_description(self, name):
        for param, description in self.params:
            if param == name:
                return description
        else:
            return ''

comment_start_pat = re.compile(r'^\s*/\*\*\s')
comment_end_pat = re.compile(r'^\s*\*+/')
comment_line_lead = re.compile(r'^\s*\*\s*')
funcname_pat = re.compile(r'^(\w+)\s*:?')
return_pat = re.compile(r'^(returns:|return\s+value:|returns\s*)(.*\n?)$',
                        re.IGNORECASE)
param_pat = re.compile(r'^@(\S+)\s*:(.*\n?)$')

def parse_file(fp, doc_dict):
    line = fp.readline()
    in_comment_block = 0
    while line:
        if not in_comment_block:
            if comment_start_pat.match(line):
                in_comment_block = 1
                cur_doc = FunctionDoc()
                in_description = 0
                in_return = 0
            line = fp.readline()
            continue

        # we are inside a comment block ...
        if comment_end_pat.match(line):
            if not cur_doc.name:
                sys.stderr.write("no function name found in doc comment\n")
            else:
                doc_dict[cur_doc.name] = cur_doc
            in_comment_block = 0
            line = fp.readline()
            continue

        # inside a comment block, and not the end of the block ...
        line = comment_line_lead.sub('', line)
        if not line: line = '\n'

        if not cur_doc.name:
            match = funcname_pat.match(line)
            if match:
                cur_doc.set_name(match.group(1))
        elif in_return:
            match = return_pat.match(line)
            if match:
                # assume the last return statement was really part of the
                # description
                return_start = match.group(1)
                cur_doc.ret = match.group(2)
                cur_doc.description = cur_doc.description + return_start + \
                                      cur_doc.ret
            else:
                cur_doc.append_return(line)
        elif in_description:
            if line[:12] == 'Description:':
                line = line[12:]
            match = return_pat.match(line)
            if match:
                in_return = 1
                return_start = match.group(1)
                cur_doc.append_return(match.group(2))
            else:
                cur_doc.append_description(line)
        elif line == '\n':
            # end of parameters
            in_description = 1
        else:
            match = param_pat.match(line)
            if match:
                param = match.group(1)
                desc = match.group(2)
                if param == 'returns':
                    cur_doc.ret = desc
                else:
                    cur_doc.add_param(param, desc)
            else:
                # must be continuation
                try:
                    if param == 'returns':
                        cur_doc.append_return(line)
                    else:
                        cur_doc.append_to_last_param(line)
                except:
                    sys.stderr.write('something weird while reading param\n')
        line = fp.readline()

def parse_dir(dir, doc_dict):
    for file in os.listdir(dir):
        if file in ('.', '..'): continue
        path = os.path.join(dir, file)
        if os.path.isdir(path):
            parse_dir(path, doc_dict)
        if len(file) > 2 and file[-2:] == '.c':
            parse_file(open(path, 'r'), doc_dict)

def extract(dirs, doc_dict=None):
    if not doc_dict: doc_dict = {}
    for dir in dirs:
        parse_dir(dir, doc_dict)
    return doc_dict

tmpl_section_pat = re.compile(r'^<!-- ##### (\w+) (\w+) ##### -->$')
def parse_tmpl(fp, doc_dict):
    cur_doc = None

    line = fp.readline()
    while line:
        match = tmpl_section_pat.match(line)
        if match:
            cur_doc = None  # new input shouldn't affect the old doc dict
            sect_type = match.group(1)
            sect_name = match.group(2)

            if sect_type == 'FUNCTION':
                cur_doc = doc_dict.get(sect_name)
                if not cur_doc:
                    cur_doc = FunctionDoc()
                    cur_doc.set_name(sect_name)
                    doc_dict[sect_name] = cur_doc
        elif line == '<!-- # Unused Parameters # -->\n':
            cur_doc = None # don't worry about unused params.
        elif cur_doc:
            if line[:10] == '@Returns: ':
                if string.strip(line[10:]):
                    cur_doc.append_return(line[10:])
            elif line[0] == '@':
                pos = string.find(line, ':')
                if pos >= 0:
                    cur_doc.append_to_named_param(line[1:pos], line[pos+1:])
                else:
                    cur_doc.append_description(line)
            else:
                cur_doc.append_description(line)

        line = fp.readline()

def extract_tmpl(dirs, doc_dict=None):
    if not doc_dict: doc_dict = {}
    for dir in dirs:
        for file in os.listdir(dir):
            if file in ('.', '..'): continue
            path = os.path.join(dir, file)
            if os.path.isdir(path):
                continue
            if len(file) > 2 and file[-2:] == '.sgml':
                parse_tmpl(open(path, 'r'), doc_dict)
    return doc_dict
