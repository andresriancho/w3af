#!/usr/bin/env python
# -*- Mode: Python; py-indent-offset: 4 -*-
import sys, os, string, re, getopt

import defsparser
import definitions
import override
import docextract

class Node:
    def __init__(self, name, interfaces=[]):
        self.name = name
        self.interfaces = interfaces
        self.subclasses = []
    def add_child(self, node):
        self.subclasses.append(node)

def build_object_tree(parser):
    # reorder objects so that parent classes come first ...
    objects = parser.objects[:]
    pos = 0
    while pos < len(objects):
        parent = objects[pos].parent
        for i in range(pos+1, len(objects)):
            if objects[i].c_name == parent:
                objects.insert(i+1, objects[pos])
                del objects[pos]
                break
        else:
            pos = pos + 1

    root = Node(None)
    nodes = { None: root }
    for obj_def in objects:
        parent_node = nodes[obj_def.parent]
        node = Node(obj_def.c_name, obj_def.implements)
        parent_node.add_child(node)
        nodes[node.name] = node

    if parser.interfaces:
        interfaces = Node('gobject.GInterface')
        root.add_child(interfaces)
        nodes[interfaces.name] = interfaces
        for obj_def in parser.interfaces:
            node = Node(obj_def.c_name)
            interfaces.add_child(node)
            nodes[node.name] = node

    if parser.boxes:
        boxed = Node('gobject.GBoxed')
        root.add_child(boxed)
        nodes[boxed.name] = boxed
        for obj_def in parser.boxes:
            node = Node(obj_def.c_name)
            boxed.add_child(node)
            nodes[node.name] = node

    if parser.pointers:
        pointers = Node('gobject.GPointer')
        root.add_child(pointers)
        nodes[pointers.name] = pointers
        for obj_def in parser.pointers:
            node = Node(obj_def.c_name)
            pointers.add_child(node)
            nodes[node.name] = node

    return root

class DocWriter:
    def __init__(self):
        # parse the defs file
        self.parser = defsparser.DefsParser(())
        self.overrides = override.Overrides()
        self.classmap = {}
        self.docs = {}

    def add_sourcedirs(self, source_dirs):
        self.docs = docextract.extract(source_dirs, self.docs)
    def add_tmpldirs(self, tmpl_dirs):
        self.docs = docextract.extract_tmpl(tmpl_dirs, self.docs)

    def add_docs(self, defs_file, overrides_file, module_name):
        '''parse information about a given defs file'''
        self.parser.filename = defs_file
        self.parser.startParsing(defs_file)
        if overrides_file:
            self.overrides.handle_file(overrides_file)

        for obj in self.parser.objects:
            if not self.classmap.has_key(obj.c_name):
                self.classmap[obj.c_name] = '%s.%s' % (module_name, obj.name)
        for obj in self.parser.interfaces:
            if not self.classmap.has_key(obj.c_name):
                self.classmap[obj.c_name] = '%s.%s' % (module_name, obj.name)
        for obj in self.parser.boxes:
            if not self.classmap.has_key(obj.c_name):
                self.classmap[obj.c_name] = '%s.%s' % (module_name, obj.name)
        for obj in self.parser.pointers:
            if not self.classmap.has_key(obj.c_name):
                self.classmap[obj.c_name] = '%s.%s' % (module_name, obj.name)

    def pyname(self, name):
        return self.classmap.get(name, name)

    def __compare(self, obja, objb):
        return cmp(self.pyname(obja.c_name), self.pyname(objb.c_name))
    def output_docs(self, output_prefix):
        files = []

        # class hierarchy
        hierarchy = build_object_tree(self.parser)
        filename = self.create_filename('hierarchy', output_prefix)
        fp = open(filename, 'w')
        self.write_full_hierarchy(hierarchy, fp)
        fp.close()

        obj_defs = self.parser.objects + self.parser.interfaces + \
                   self.parser.boxes + self.parser.pointers
        obj_defs.sort(self.__compare)
        for obj_def in obj_defs:
            filename = self.create_filename(obj_def.c_name, output_prefix)
            fp = open(filename, 'w')
            if isinstance(obj_def, definitions.ObjectDef):
                self.output_object_docs(obj_def, fp)
            elif isinstance(obj_def, definitions.InterfaceDef):
                self.output_interface_docs(obj_def, fp)
            elif isinstance(obj_def, definitions.BoxedDef):
                self.output_boxed_docs(obj_def, fp)
            elif isinstance(obj_def, definitions.PointerDef):
                self.output_boxed_docs(obj_def, fp)
            fp.close()
            files.append((os.path.basename(filename), obj_def))

        if files:
            filename = self.create_toc_filename(output_prefix)
            fp = open(filename, 'w')
            self.output_toc(files, fp)
            fp.close()

    def output_object_docs(self, obj_def, fp=sys.stdout):
        self.write_class_header(obj_def.c_name, fp)

        self.write_heading('Synopsis', fp)
        self.write_synopsis(obj_def, fp)
        self.close_section(fp)

        # construct the inheritence hierarchy ...
        ancestry = [ (obj_def.c_name, obj_def.implements) ]
        try:
            parent = obj_def.parent
            while parent != None:
                if parent == 'GObject':
                    ancestry.append(('GObject', []))
                    parent = None
                else:
                    parent_def = self.parser.find_object(parent)
                    ancestry.append((parent_def.c_name, parent_def.implements))
                    parent = parent_def.parent
        except ValueError:
            pass
        ancestry.reverse()
        self.write_heading('Ancestry', fp)
        self.write_hierarchy(obj_def.c_name, ancestry, fp)
        self.close_section(fp)

        constructor = self.parser.find_constructor(obj_def, self.overrides)
        if constructor:
            self.write_heading('Constructor', fp)
            self.write_constructor(constructor,
                                   self.docs.get(constructor.c_name, None),
                                   fp)
            self.close_section(fp)

        methods = self.parser.find_methods(obj_def)
        methods = filter(lambda meth, self=self:
                         not self.overrides.is_ignored(meth.c_name), methods)
        if methods:
            self.write_heading('Methods', fp)
            for method in methods:
                self.write_method(method, self.docs.get(method.c_name, None), fp)
            self.close_section(fp)

        self.write_class_footer(obj_def.c_name, fp)

    def output_interface_docs(self, int_def, fp=sys.stdout):
        self.write_class_header(int_def.c_name, fp)

        self.write_heading('Synopsis', fp)
        self.write_synopsis(int_def, fp)
        self.close_section(fp)

        methods = self.parser.find_methods(int_def)
        methods = filter(lambda meth, self=self:
                         not self.overrides.is_ignored(meth.c_name), methods)
        if methods:
            self.write_heading('Methods', fp)
            for method in methods:
                self.write_method(method, self.docs.get(method.c_name, None), fp)
            self.close_section(fp)

        self.write_class_footer(int_def.c_name, fp)

    def output_boxed_docs(self, box_def, fp=sys.stdout):
        self.write_class_header(box_def.c_name, fp)

        self.write_heading('Synopsis', fp)
        self.write_synopsis(box_def, fp)
        self.close_section(fp)

        constructor = self.parser.find_constructor(box_def, self.overrides)
        if constructor:
            self.write_heading('Constructor', fp)
            self.write_constructor(constructor,
                                   self.docs.get(constructor.c_name, None),
                                   fp)
            self.close_section(fp)

        methods = self.parser.find_methods(box_def)
        methods = filter(lambda meth, self=self:
                         not self.overrides.is_ignored(meth.c_name), methods)
        if methods:
            self.write_heading('Methods', fp)
            for method in methods:
                self.write_method(method, self.docs.get(method.c_name, None), fp)
            self.close_section(fp)

        self.write_class_footer(box_def.c_name, fp)

    def output_toc(self, files, fp=sys.stdout):
        fp.write('TOC\n\n')
        for filename, obj_def in files:
            fp.write(obj_def.c_name + ' - ' + filename + '\n')

    # override the following to create a more complex output format
    def create_filename(self, obj_name, output_prefix):
        '''Create output filename for this particular object'''
        return output_prefix + '-' + string.lower(obj_name) + '.txt'
    def create_toc_filename(self, output_prefix):
        return self.create_filename(self, 'docs', output_prefix)

    def write_full_hierarchy(self, hierarchy, fp):
        def handle_node(node, fp, indent=''):
            for child in node.subclasses:
                fp.write(indent + node.name)
                if node.interfaces:
                    fp.write(' (implements ')
                    fp.write(string.join(node.interfaces, ', '))
                    fp.write(')\n')
                else:
                    fp.write('\n')
                handle_node(child, fp, indent + '  ')
        handle_node(hierarchy, fp)

    # these need to handle default args ...
    def create_constructor_prototype(self, func_def):
        return func_def.is_constructor_of + '(' + \
               string.join(map(lambda x: x[1], func_def.params), ', ') + \
               ')'
    def create_function_prototype(self, func_def):
        return func_def.name + '(' + \
               string.join(map(lambda x: x[1], func_def.params), ', ') + \
               ')'
    def create_method_prototype(self, meth_def):
        return meth_def.of_object + '.' + \
               meth_def.name + '(' + \
               string.join(map(lambda x: x[1], meth_def.params), ', ') + \
               ')'

    def write_class_header(self, obj_name, fp):
        fp.write('Class %s\n' % obj_name)
        fp.write('======%s\n\n' % ('=' * len(obj_name)))
    def write_class_footer(self, obj_name, fp):
        pass
    def write_heading(self, text, fp):
        fp.write('\n' + text + '\n' + ('-' * len(text)) + '\n')
    def close_section(self, fp):
        pass
    def write_synopsis(self, obj_def, fp):
        fp.write('class %s' % obj_def.c_name)
        if isinstance(obj_def, definitions.ObjectDef):
            bases = []
            if obj_def.parent: bases.append(obj_def.parent)
            bases = bases = obj_def.implements
            if bases:
                fp.write('(%s)' % string.join(bases, ', '))
        fp.write(':\n')

        constructor = self.parser.find_constructor(obj_def, self.overrides)
        if constructor:
            prototype = self.create_constructor_prototype(constructor)
            fp.write('    def %s\n' % prototype)
        methods = self.parser.find_methods(obj_def)
        methods = filter(lambda meth, self=self:
                         not self.overrides.is_ignored(meth.c_name), methods)
        for meth in methods:
            prototype = self.create_method_prototype(meth)
            fp.write('    def %s\n' % prototype)

    def write_hierarchy(self, obj_name, ancestry, fp):
        indent = ''
        for name, interfaces in ancestry:
            fp.write(indent + '+-- ' + name)
            if interfaces:
                fp.write(' (implements ')
                fp.write(string.join(interfaces, ', '))
                fp.write(')\n')
            else:
                fp.write('\n')
            indent = indent + '  '
        fp.write('\n')
    def write_constructor(self, func_def, func_doc, fp):
        prototype = self.create_constructor_prototype(func_def)
        fp.write(prototype + '\n\n')
        for type, name, dflt, null in func_def.params:
            if func_doc:
                descr = func_doc.get_param_description(name)
            else:
                descr = 'a ' + type
            fp.write('  ' + name + ': ' + descr + '\n')
        if func_def.ret and func_def.ret != 'none':
            if func_doc and func_doc.ret:
                descr = func_doc.ret
            else:
                descr = 'a ' + func_def.ret
            fp.write('  Returns: ' + descr + '\n')
        if func_doc and func_doc.description:
            fp.write(func_doc.description)
        fp.write('\n\n\n')
    def write_method(self, meth_def, func_doc, fp):
        prototype = self.create_method_prototype(meth_def)
        fp.write(prototype + '\n\n')
        for type, name, dflt, null in meth_def.params:
            if func_doc:
                descr = func_doc.get_param_description(name)
            else:
                descr = 'a ' + type
            fp.write('  ' + name + ': ' + descr + '\n')
        if meth_def.ret and meth_def.ret != 'none':
            if func_doc and func_doc.ret:
                descr = func_doc.ret
            else:
                descr = 'a ' + meth_def.ret
            fp.write('  Returns: ' + descr + '\n')
        if func_doc and func_doc.description:
            fp.write('\n')
            fp.write(func_doc.description)
        fp.write('\n\n')

class DocbookDocWriter(DocWriter):
    def __init__(self, use_xml=0):
        DocWriter.__init__(self)
        self.use_xml = use_xml

    def create_filename(self, obj_name, output_prefix):
        '''Create output filename for this particular object'''
        stem = output_prefix + '-' + string.lower(obj_name)
        if self.use_xml:
            return stem + '.xml'
        else:
            return stem + '.sgml'
    def create_toc_filename(self, output_prefix):
        if self.use_xml:
            return self.create_filename('classes', output_prefix)
        else:
            return self.create_filename('docs', output_prefix)

    # make string -> reference translation func
    __transtable = [ '-' ] * 256
    for digit in '0123456789':
        __transtable[ord(digit)] = digit
    for letter in 'abcdefghijklmnopqrstuvwxyz':
        __transtable[ord(letter)] = letter
        __transtable[ord(string.upper(letter))] = letter
    __transtable = string.join(__transtable, '')

    def make_class_ref(self, obj_name):
        return 'class-' + string.translate(obj_name, self.__transtable)
    def make_method_ref(self, meth_def):
        return 'method-' + string.translate(meth_def.of_object,
                                            self.__transtable) + \
            '--' + string.translate(meth_def.name, self.__transtable)

    __function_pat = re.compile(r'(\w+)\s*\(\)')
    def __format_function(self, match):
        info = self.parser.c_name.get(match.group(1), None)
        if info:
            if isinstance(info, defsparser.FunctionDef):
                if info.is_constructor_of is not None:
                    # should have a link here
                    return '<function>%s()</function>' % \
                           self.pyname(info.is_constructor_of)
                else:
                    return '<function>' + info.name + '()</function>'
            if isinstance(info, defsparser.MethodDef):
                return '<link linkend="' + self.make_method_ref(info) + \
                       '"><function>' + self.pyname(info.of_object) + '.' + \
                       info.name + '()</function></link>'
        # fall through through
        return '<function>' + match.group(1) + '()</function>'
    __parameter_pat = re.compile(r'\@(\w+)')
    def __format_param(self, match):
        return '<parameter>' + match.group(1) + '</parameter>'
    __constant_pat = re.compile(r'\%(-?\w+)')
    def __format_const(self, match):
        return '<literal>' + match.group(1) + '</literal>'
    __symbol_pat = re.compile(r'#([\w-]+)')
    def __format_symbol(self, match):
        info = self.parser.c_name.get(match.group(1), None)
        if info:
            if isinstance(info, defsparser.FunctionDef):
                if info.is_constructor_of is not None:
                    # should have a link here
                    return '<methodname>' + self.pyname(info.is_constructor_of) + \
                           '</methodname>'
                else:
                    return '<function>' + info.name + '</function>'
            if isinstance(info, defsparser.MethodDef):
                return '<link linkend="' + self.make_method_ref(info) + \
                       '"><methodname>' + self.pyname(info.of_object) + '.' + \
                       info.name + '</methodname></link>'
            if isinstance(info, defsparser.ObjectDef) or \
                   isinstance(info, defsparser.InterfaceDef) or \
                   isinstance(info, defsparser.BoxedDef) or \
                   isinstance(info, defsparser.PointerDef):
                return '<link linkend="' + self.make_class_ref(info.c_name) + \
                       '"><classname>' + self.pyname(info.c_name) + \
                       '</classname></link>'
        # fall through through
        return '<literal>' + match.group(1) + '</literal>'

    def reformat_text(self, text, singleline=0):
        # replace special strings ...
        text = self.__function_pat.sub(self.__format_function, text)
        text = self.__parameter_pat.sub(self.__format_param, text)
        text = self.__constant_pat.sub(self.__format_const, text)
        text = self.__symbol_pat.sub(self.__format_symbol, text)

        # don't bother with <para> expansion for single line text.
        if singleline: return text

        lines = string.split(string.strip(text), '\n')
        for index in range(len(lines)):
            if string.strip(lines[index]) == '':
                lines[index] = '</para>\n<para>'
                continue
        lines.insert(0, '<para>')
        lines.append('</para>')
        return string.join(lines, '\n')

    # write out hierarchy
    def write_full_hierarchy(self, hierarchy, fp):
        def handle_node(node, fp, indent=''):
            if node.name:
                fp.write('%s<link linkend="%s">%s</link>' %
                         (indent, self.make_class_ref(node.name),
                          self.pyname(node.name)))
                if node.interfaces:
                    fp.write(' (implements ')
                    for i in range(len(node.interfaces)):
                        fp.write('<link linkend="%s">%s</link>' %
                                 (self.make_class_ref(node.interfaces[i]),
                                  self.pyname(node.interfaces[i])))
                        if i != len(node.interfaces) - 1:
                            fp.write(', ')
                    fp.write(')\n')
                else:
                    fp.write('\n')

                indent = indent + '  '
            node.subclasses.sort(lambda a,b:
                                 cmp(self.pyname(a.name), self.pyname(b.name)))
            for child in node.subclasses:
                handle_node(child, fp, indent)
        if self.use_xml:
            fp.write('<?xml version="1.0" standalone="no"?>\n')
            fp.write('<!DOCTYPE synopsis PUBLIC "-//OASIS//DTD DocBook XML V4.1.2//EN"\n')
            fp.write('    "http://www.oasis-open.org/docbook/xml/4.1.2/docbookx.dtd">\n')
        fp.write('<synopsis>')
        handle_node(hierarchy, fp)
        fp.write('</synopsis>\n')

    # these need to handle default args ...
    def create_constructor_prototype(self, func_def):
        sgml = [ '<constructorsynopsis language="python">\n']
        sgml.append('    <methodname>__init__</methodname>\n')
        for type, name, dflt, null in func_def.params:
            sgml.append('    <methodparam><parameter>')
            sgml.append(name)
            sgml.append('</parameter>')
            if dflt:
                sgml.append('<initializer>')
                sgml.append(dflt)
                sgml.append('</initializer>')
            sgml.append('</methodparam>\n')
        if not func_def.params:
            sgml.append('    <methodparam></methodparam>')
        sgml.append('  </constructorsynopsis>')
        return string.join(sgml, '')
    def create_function_prototype(self, func_def):
        sgml = [ '<funcsynopsis language="python">\n    <funcprototype>\n']
        sgml.append('      <funcdef><function>')
        sgml.append(func_def.name)
        sgml.append('</function></funcdef>\n')
        for type, name, dflt, null in func_def.params:
            sgml.append('      <paramdef><parameter>')
            sgml.append(name)
            sgml.append('</parameter>')
            if dflt:
                sgml.append('<initializer>')
                sgml.append(dflt)
                sgml.append('</initializer>')
            sgml.append('</paramdef>\n')
        if not func_def.params:
            sgml.append('      <paramdef></paramdef')
        sgml.append('    </funcprototype>\n  </funcsynopsis>')
        return string.join(sgml, '')
    def create_method_prototype(self, meth_def, addlink=0):
        sgml = [ '<methodsynopsis language="python">\n']
        sgml.append('    <methodname>')
        if addlink:
            sgml.append('<link linkend="%s">' % self.make_method_ref(meth_def))
        sgml.append(self.pyname(meth_def.name))
        if addlink:
            sgml.append('</link>')
        sgml.append('</methodname>\n')
        for type, name, dflt, null in meth_def.params:
            sgml.append('    <methodparam><parameter>')
            sgml.append(name)
            sgml.append('</parameter>')
            if dflt:
                sgml.append('<initializer>')
                sgml.append(dflt)
                sgml.append('</initializer>')
            sgml.append('</methodparam>\n')
        if not meth_def.params:
            sgml.append('    <methodparam></methodparam>')
        sgml.append('  </methodsynopsis>')
        return string.join(sgml, '')

    def write_class_header(self, obj_name, fp):
        if self.use_xml:
            fp.write('<?xml version="1.0" standalone="no"?>\n')
            fp.write('<!DOCTYPE refentry PUBLIC "-//OASIS//DTD DocBook XML V4.1.2//EN"\n')
            fp.write('    "http://www.oasis-open.org/docbook/xml/4.1.2/docbookx.dtd">\n')
        fp.write('<refentry id="' + self.make_class_ref(obj_name) + '">\n')
        fp.write('  <refmeta>\n')
        fp.write('    <refentrytitle>%s</refentrytitle>\n'
                 % self.pyname(obj_name))
        fp.write('    <manvolnum>3</manvolnum>\n')
        fp.write('    <refmiscinfo>PyGTK Docs</refmiscinfo>\n')
        fp.write('  </refmeta>\n\n')
        fp.write('  <refnamediv>\n')
        fp.write('    <refname>%s</refname><refpurpose></refpurpose>\n'
                 % self.pyname(obj_name))
        fp.write('  </refnamediv>\n\n')
    def write_class_footer(self, obj_name, fp):
        fp.write('</refentry>\n')
    def write_heading(self, text, fp):
        fp.write('  <refsect1>\n')
        fp.write('    <title>' + text + '</title>\n\n')
    def close_section(self, fp):
        fp.write('  </refsect1>\n')

    def write_synopsis(self, obj_def, fp):
        fp.write('<classsynopsis language="python">\n')
        fp.write('  <ooclass><classname>%s</classname></ooclass>\n'
                 % self.pyname(obj_def.c_name))
        if isinstance(obj_def, definitions.ObjectDef):
            if obj_def.parent:
                fp.write('  <ooclass><classname><link linkend="%s">%s'
                         '</link></classname></ooclass>\n'
                         % (self.make_class_ref(obj_def.parent),
                            self.pyname(obj_def.parent)))
            for base in obj_def.implements:
                fp.write('  <ooclass><classname><link linkend="%s">%s'
                         '</link></classname></ooclass>\n'
                         % (self.make_class_ref(base), self.pyname(base)))
        elif isinstance(obj_def, definitions.InterfaceDef):
            fp.write('  <ooclass><classname>gobject.GInterface'
                     '</classname></ooclass>\n')
        elif isinstance(obj_def, definitions.BoxedDef):
            fp.write('  <ooclass><classname>gobject.GBoxed'
                     '</classname></ooclass>\n')
        elif isinstance(obj_def, definitions.PointerDef):
            fp.write('  <ooclass><classname>gobject.GPointer'
                     '</classname></ooclass>\n')

        constructor = self.parser.find_constructor(obj_def, self.overrides)
        if constructor:
            fp.write('%s\n' % self.create_constructor_prototype(constructor))
        methods = self.parser.find_methods(obj_def)
        methods = filter(lambda meth, self=self:
                         not self.overrides.is_ignored(meth.c_name), methods)
        for meth in methods:
            fp.write('%s\n' % self.create_method_prototype(meth, addlink=1))
        fp.write('</classsynopsis>\n\n')

    def write_hierarchy(self, obj_name, ancestry, fp):
        fp.write('<synopsis>')
        indent = ''
        for name, interfaces in ancestry:
            fp.write(indent + '+-- <link linkend="' +
                     self.make_class_ref(name) + '">'+ self.pyname(name) + '</link>')
            if interfaces:
                fp.write(' (implements ')
                for i in range(len(interfaces)):
                    fp.write('<link linkend="%s">%s</link>' %
                             (self.make_class_ref(interfaces[i]),
                              self.pyname(interfaces[i])))
                    if i != len(interfaces) - 1:
                        fp.write(', ')
                fp.write(')\n')
            else:
                fp.write('\n')
            indent = indent + '  '
        fp.write('</synopsis>\n\n')

    def write_params(self, params, ret, func_doc, fp):
        if not params and (not ret or ret == 'none'):
            return
        fp.write('  <variablelist>\n')
        for type, name, dflt, null in params:
            if func_doc:
                descr = string.strip(func_doc.get_param_description(name))
            else:
                descr = 'a ' + type
            fp.write('    <varlistentry>\n')
            fp.write('      <term><parameter>%s</parameter>&nbsp;:</term>\n' % name)
            fp.write('      <listitem><simpara>%s</simpara></listitem>\n' %
                     self.reformat_text(descr, singleline=1))
            fp.write('    </varlistentry>\n')
        if ret and ret != 'none':
            if func_doc and func_doc.ret:
                descr = string.strip(func_doc.ret)
            else:
                descr = 'a ' + ret
            fp.write('    <varlistentry>\n')
            fp.write('      <term><emphasis>Returns</emphasis>&nbsp;:</term>\n')
            fp.write('      <listitem><simpara>%s</simpara></listitem>\n' %
                     self.reformat_text(descr, singleline=1))
            fp.write('    </varlistentry>\n')
        fp.write('  </variablelist>\n')

    def write_constructor(self, func_def, func_doc, fp):
        prototype = self.create_constructor_prototype(func_def)
        fp.write('<programlisting>%s</programlisting>\n' % prototype)
        self.write_params(func_def.params, func_def.ret, func_doc, fp)

        if func_doc and func_doc.description:
            fp.write(self.reformat_text(func_doc.description))
        fp.write('\n\n\n')

    def write_method(self, meth_def, func_doc, fp):
        fp.write('  <refsect2 id="' + self.make_method_ref(meth_def) + '">\n')
        fp.write('    <title>' + self.pyname(meth_def.of_object) + '.' +
                 meth_def.name + '</title>\n\n')
        prototype = self.create_method_prototype(meth_def)
        fp.write('<programlisting>%s</programlisting>\n' % prototype)
        self.write_params(meth_def.params, meth_def.ret, func_doc, fp)
        if func_doc and func_doc.description:
            fp.write(self.reformat_text(func_doc.description))
        fp.write('  </refsect2>\n\n\n')

    def output_toc(self, files, fp=sys.stdout):
        if self.use_xml:
            fp.write('<?xml version="1.0" standalone="no"?>\n')
            fp.write('<!DOCTYPE reference PUBLIC "-//OASIS//DTD DocBook XML V4.1.2//EN"\n')
            fp.write('    "http://www.oasis-open.org/docbook/xml/4.1.2/docbookx.dtd">\n')
            #for filename, obj_def in files:
            #    fp.write('  <!ENTITY ' + string.translate(obj_def.c_name,
            #                                              self.__transtable) +
            #             ' SYSTEM "' + filename + '" >\n')
            #fp.write(']>\n\n')

            #fp.write('<reference id="class-reference">\n')
            #fp.write('  <title>Class Documentation</title>\n')
            #for filename, obj_def in files:
            #    fp.write('&' + string.translate(obj_def.c_name,
            #                                    self.__transtable) + ';\n')
            #fp.write('</reference>\n')

            fp.write('<reference id="class-reference" xmlns:xi="http://www.w3.org/2001/XInclude">\n')
            fp.write('  <title>Class Reference</title>\n')
            for filename, obj_def in files:
                fp.write('  <xi:include href="%s"/>\n' % filename)
            fp.write('</reference>\n')
        else:
            fp.write('<!DOCTYPE article PUBLIC "-//OASIS//DTD DocBook V4.1.2//EN" [\n')
            for filename, obj_def in files:
                fp.write('  <!ENTITY ' + string.translate(obj_def.c_name,
                                                          self.__transtable) +
                         ' SYSTEM "' + filename + '" >\n')
            fp.write(']>\n\n')

            fp.write('<book id="index">\n\n')
            fp.write('  <bookinfo>\n')
            fp.write('    <title>PyGTK Docs</title>\n')
            fp.write('    <authorgroup>\n')
            fp.write('      <author>\n')
            fp.write('        <firstname>James</firstname>\n')
            fp.write('        <surname>Henstridge</surname>\n')
            fp.write('      </author>\n')
            fp.write('    </authorgroup>\n')
            fp.write('  </bookinfo>\n\n')

            fp.write('  <chapter id="class-hierarchy">\n')
            fp.write('    <title>Class Hierarchy</title>\n')
            fp.write('    <para>Not done yet</para>\n')
            fp.write('  </chapter>\n\n')

            fp.write('  <reference id="class-reference">\n')
            fp.write('    <title>Class Documentation</title>\n')
            for filename, obj_def in files:
                fp.write('&' + string.translate(obj_def.c_name,
                                                self.__transtable) + ';\n')

            fp.write('  </reference>\n')
            fp.write('</book>\n')

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:s:o:",
                                   ["defs-file=", "override=", "source-dir=",
                                    "output-prefix="])
    except getopt.error, e:
        sys.stderr.write('docgen.py: %s\n' % e)
        sys.stderr.write(
            'usage: docgen.py -d file.defs [-s /src/dir] [-o output-prefix]\n')
        sys.exit(1)
    defs_file = None
    overrides_file = None
    source_dirs = []
    output_prefix = 'docs'
    for opt, arg in opts:
        if opt in ('-d', '--defs-file'):
            defs_file = arg
        if opt in ('--override',):
            overrides_file = arg
        elif opt in ('-s', '--source-dir'):
            source_dirs.append(arg)
        elif opt in ('-o', '--output-prefix'):
            output_prefix = arg
    if len(args) != 0 or not defs_file:
        sys.stderr.write(
            'usage: docgen.py -d file.defs [-s /src/dir] [-o output-prefix]\n')
        sys.exit(1)

    d = DocbookDocWriter()
    d.add_sourcedirs(source_dirs)
    d.add_docs(defs_file, overrides_file, 'gtk')
    d.output_docs(output_prefix)
