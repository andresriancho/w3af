# -*- Mode: Python; py-indent-offset: 4 -*-

# this file contains code for loading up an override file.  The override file
# provides implementations of functions where the code generator could not
# do its job correctly.

import fnmatch
import os
import re
import string
import sys

def class2cname(klass, method):
    c_name = ''
    for c in klass:
        if c.isupper():
            c_name += '_' + c.lower()
        else:
            c_name += c
    return c_name[1:] + '_'  + method

import_pat = re.compile(r'\s*import\s+(\S+)\.([^\s.]+)\s+as\s+(\S+)')

class Overrides:
    def __init__(self, filename=None):
        self.modulename = None
        self.ignores = {}
        self.glob_ignores = []
        self.type_ignores = {}
        self.overrides = {}
        self.overridden = {}
        self.kwargs = {}
        self.noargs = {}
        self.onearg = {}
        self.staticmethod = {}
        self.classmethod = {}
        self.startlines = {}
        self.override_attrs = {}
        self.override_slots = {}
        self.headers = ''
        self.body = ''
        self.init = ''
        self.imports = []
        self.defines = {}
        self.functions = {}
        self.newstyle_constructors = {}
        self.dynamicnamespace = False
        if filename:
            self.handle_file(filename)

    def handle_file(self, filename):
        oldpath = os.getcwd()

        fp = open(filename, 'r')
        dirname = os.path.dirname(os.path.abspath(filename))

        if dirname != oldpath:
            os.chdir(dirname)

        # read all the components of the file ...
        bufs = []
        startline = 1
        lines = []
        line = fp.readline()
        linenum = 1
        while line:
            if line == '%%\n' or line == '%%':
                if lines:
                    bufs.append((string.join(lines, ''), startline))
                startline = linenum + 1
                lines = []
            else:
                lines.append(line)
            line = fp.readline()
            linenum = linenum + 1
        if lines:
            bufs.append((string.join(lines, ''), startline))
        if not bufs: return

        for buf, startline in bufs:
            self.__parse_override(buf, startline, filename)

        os.chdir(oldpath)

    def __parse_override(self, buffer, startline, filename):
        pos = string.find(buffer, '\n')
        if pos >= 0:
            line = buffer[:pos]
            rest = buffer[pos+1:]
        else:
            line = buffer ; rest = ''
        words = string.split(line)
        command = words[0]
        if (command == 'ignore' or
            command == 'ignore-' + sys.platform):
            "ignore/ignore-platform [functions..]"
            for func in words[1:]:
                self.ignores[func] = 1
            for func in string.split(rest):
                self.ignores[func] = 1
        elif (command == 'ignore-glob' or
              command == 'ignore-glob-' + sys.platform):
            "ignore-glob/ignore-glob-platform [globs..]"
            for func in words[1:]:
                self.glob_ignores.append(func)
            for func in string.split(rest):
                self.glob_ignores.append(func)
        elif (command == 'ignore-type' or
              command == 'ignore-type-' + sys.platform):
            "ignore-type/ignore-type-platform [typenames..]"
            for typename in words[1:]:
                self.type_ignores[typename] = 1
            for typename in string.split(rest):
                self.type_ignores[typename] = 1
        elif command == 'override':
            "override function/method [kwargs|noargs|onearg] [staticmethod|classmethod]"
            func = words[1]
            if 'kwargs' in words[1:]:
                self.kwargs[func] = 1
            elif 'noargs' in words[1:]:
                self.noargs[func] = 1
            elif 'onearg' in words[1:]:
                self.onearg[func] = True

            if 'staticmethod' in words[1:]:
                self.staticmethod[func] = True
            elif 'classmethod' in words[1:]:
                self.classmethod[func] = True
            if func in self.overrides:
                raise RuntimeError("Function %s is being overridden more than once" % (func,))
            self.overrides[func] = rest
            self.startlines[func] = (startline + 1, filename)
        elif command == 'override-attr':
            "override-slot Class.attr"
            attr = words[1]
            self.override_attrs[attr] = rest
            self.startlines[attr] = (startline + 1, filename)
        elif command == 'override-slot':
            "override-slot Class.slot"
            slot = words[1]
            self.override_slots[slot] = rest
            self.startlines[slot] = (startline + 1, filename)
        elif command == 'headers':
            "headers"
            self.headers = '%s\n#line %d "%s"\n%s' % \
                           (self.headers, startline + 1, filename, rest)
        elif command == 'body':
            "body"
            self.body = '%s\n#line %d "%s"\n%s' % \
                           (self.body, startline + 1, filename, rest)
        elif command == 'init':
            "init"
            self.init = '%s\n#line %d "%s"\n%s' % \
                        (self.init, startline + 1, filename, rest)
        elif command == 'modulename':
            "modulename name"
            self.modulename = words[1]
        elif command == 'include':
            "include filename"
            for filename in words[1:]:
                self.handle_file(filename)
            for filename in string.split(rest):
                self.handle_file(filename)
        elif command == 'import':
            "import module1 [\n module2, \n module3 ...]"
            for line in string.split(buffer, '\n'):
                match = import_pat.match(line)
                if match:
                    self.imports.append(match.groups())
        elif command == 'define':
            "define funcname [kwargs|noargs|onearg] [classmethod|staticmethod]"
            "define Class.method [kwargs|noargs|onearg] [classmethod|staticmethod]"
            func = words[1]
            klass = None
            if func.find('.') != -1:
                klass, func = func.split('.', 1)

                if not self.defines.has_key(klass):
                    self.defines[klass] = {}
                self.defines[klass][func] = rest
            else:
                self.functions[func] = rest

            if 'kwargs' in words[1:]:
                self.kwargs[func] = 1
            elif 'noargs' in words[1:]:
                self.noargs[func] = 1
            elif 'onearg' in words[1:]:
                self.onearg[func] = 1

            if 'staticmethod' in words[1:]:
                self.staticmethod[func] = True
            elif 'classmethod' in words[1:]:
                self.classmethod[func] = True

            self.startlines[func] = (startline + 1, filename)

        elif command == 'new-constructor':
            "new-constructor GType"
            gtype, = words[1:]
            self.newstyle_constructors[gtype] = True
        elif command == 'options':
            for option in words[1:]:
                if option == 'dynamicnamespace':
                    self.dynamicnamespace = True

    def is_ignored(self, name):
        if self.ignores.has_key(name):
            return 1
        for glob in self.glob_ignores:
            if fnmatch.fnmatchcase(name, glob):
                return 1
        return 0

    def is_type_ignored(self, name):
        return name in self.type_ignores

    def is_overriden(self, name):
        return self.overrides.has_key(name)

    def is_already_included(self, name):
        return self.overridden.has_key(name)

    def override(self, name):
        self.overridden[name] = 1
        return self.overrides[name]

    def define(self, klass, name):
        self.overridden[class2cname(klass, name)] = 1
        return self.defines[klass][name]

    def function(self, name):
        return self.functions[name]

    def getstartline(self, name):
        return self.startlines[name]

    def wants_kwargs(self, name):
        return self.kwargs.has_key(name)

    def wants_noargs(self, name):
        return self.noargs.has_key(name)

    def wants_onearg(self, name):
        return self.onearg.has_key(name)

    def is_staticmethod(self, name):
        return self.staticmethod.has_key(name)

    def is_classmethod(self, name):
        return self.classmethod.has_key(name)

    def attr_is_overriden(self, attr):
        return self.override_attrs.has_key(attr)

    def attr_override(self, attr):
        return self.override_attrs[attr]

    def slot_is_overriden(self, slot):
        return self.override_slots.has_key(slot)

    def slot_override(self, slot):
        return self.override_slots[slot]

    def get_headers(self):
        return self.headers

    def get_body(self):
        return self.body

    def get_init(self):
        return self.init

    def get_imports(self):
        return self.imports

    def get_defines_for(self, klass):
        return self.defines.get(klass, {})

    def get_functions(self):
        return self.functions
