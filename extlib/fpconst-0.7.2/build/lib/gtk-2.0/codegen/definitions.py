# -*- Mode: Python; py-indent-offset: 4 -*-
import copy
import sys

def get_valid_scheme_definitions(defs):
    return [x for x in defs if isinstance(x, tuple) and len(x) >= 2]

def unescape(s):
    s = s.replace('\r\n', '\\r\\n').replace('\t', '\\t')
    return s.replace('\r', '\\r').replace('\n', '\\n')

def make_docstring(lines):
    return "(char *) " + '\n'.join(['"%s"' % unescape(s) for s in lines])

# New Parameter class, wich emulates a tuple for compatibility reasons
class Parameter(object):
    def __init__(self, ptype, pname, pdflt, pnull, pdir=None):
        self.ptype = ptype
        self.pname = pname
        self.pdflt = pdflt
        self.pnull = pnull
        self.pdir = pdir

    def __len__(self): return 4
    def __getitem__(self, i):
        return (self.ptype, self.pname, self.pdflt, self.pnull)[i]

    def merge(self, old):
        if old.pdflt is not None:
            self.pdflt = old.pdflt
        if old.pnull is not None:
            self.pnull = old.pnull

# Parameter for property based constructors
class Property(object):
    def __init__(self, pname, optional, argname):
        self.pname = pname
        self.optional = optional
        self.argname = argname

    def merge(self, old):
        if old.optional is not None:
            self.optional = old.optional
        if old.argname is not None:
            self.argname = old.argname


class Definition:
    docstring = "NULL"
    def __init__(self, *args):
        """Create a new defs object of this type.  The arguments are the
        components of the definition"""
        raise RuntimeError, "this is an abstract class"
    def merge(self, old):
        """Merge in customisations from older version of definition"""
        raise RuntimeError, "this is an abstract class"
    def write_defs(self, fp=sys.stdout):
        """write out this definition in defs file format"""
        raise RuntimeError, "this is an abstract class"

    def guess_return_value_ownership(self):
        "return 1 if caller owns return value"
        if getattr(self, 'is_constructor_of', False):
            self.caller_owns_return = True
        elif self.ret in ('char*', 'gchar*', 'string'):
            self.caller_owns_return = True
        else:
            self.caller_owns_return = False


class ObjectDef(Definition):
    def __init__(self, name, *args):
        self.name = name
        self.module = None
        self.parent = None
        self.c_name = None
        self.typecode = None
        self.fields = []
        self.implements = []
        self.class_init_func = None
        self.has_new_constructor_api = False
        for arg in get_valid_scheme_definitions(args):
            if arg[0] == 'in-module':
                self.module = arg[1]
            elif arg[0] == 'docstring':
                self.docstring = make_docstring(arg[1:])
            elif arg[0] == 'parent':
                self.parent = arg[1]
            elif arg[0] == 'c-name':
                self.c_name = arg[1]
            elif arg[0] == 'gtype-id':
                self.typecode = arg[1]
            elif arg[0] == 'fields':
                for parg in arg[1:]:
                    self.fields.append((parg[0], parg[1]))
            elif arg[0] == 'implements':
                self.implements.append(arg[1])
    def merge(self, old):
        # currently the .h parser doesn't try to work out what fields of
        # an object structure should be public, so we just copy the list
        # from the old version ...
        self.fields = old.fields
        self.implements = old.implements
    def write_defs(self, fp=sys.stdout):
        fp.write('(define-object ' + self.name + '\n')
        if self.module:
            fp.write('  (in-module "' + self.module + '")\n')
        if self.parent != (None, None):
            fp.write('  (parent "' + self.parent + '")\n')
        for interface in self.implements:
            fp.write('  (implements "' + interface + '")\n')
        if self.c_name:
            fp.write('  (c-name "' + self.c_name + '")\n')
        if self.typecode:
            fp.write('  (gtype-id "' + self.typecode + '")\n')
        if self.fields:
            fp.write('  (fields\n')
            for (ftype, fname) in self.fields:
                fp.write('    \'("' + ftype + '" "' + fname + '")\n')
            fp.write('  )\n')
        fp.write(')\n\n')

class InterfaceDef(Definition):
    def __init__(self, name, *args):
        self.name = name
        self.module = None
        self.c_name = None
        self.typecode = None
        self.vtable = None
        self.fields = []
        self.interface_info = None
        for arg in get_valid_scheme_definitions(args):
            if arg[0] == 'in-module':
                self.module = arg[1]
            elif arg[0] == 'docstring':
                self.docstring = make_docstring(arg[1:])
            elif arg[0] == 'c-name':
                self.c_name = arg[1]
            elif arg[0] == 'gtype-id':
                self.typecode = arg[1]
            elif arg[0] == 'vtable':
                self.vtable = arg[1]
        if self.vtable is None:
            self.vtable = self.c_name + "Iface"
    def write_defs(self, fp=sys.stdout):
        fp.write('(define-interface ' + self.name + '\n')
        if self.module:
            fp.write('  (in-module "' + self.module + '")\n')
        if self.c_name:
            fp.write('  (c-name "' + self.c_name + '")\n')
        if self.typecode:
            fp.write('  (gtype-id "' + self.typecode + '")\n')
        fp.write(')\n\n')

class EnumDef(Definition):
    def __init__(self, name, *args):
        self.deftype = 'enum'
        self.name = name
        self.in_module = None
        self.c_name = None
        self.typecode = None
        self.values = []
        for arg in get_valid_scheme_definitions(args):
            if arg[0] == 'in-module':
                self.in_module = arg[1]
            elif arg[0] == 'c-name':
                self.c_name = arg[1]
            elif arg[0] == 'gtype-id':
                self.typecode = arg[1]
            elif arg[0] == 'values':
                for varg in arg[1:]:
                    self.values.append((varg[0], varg[1]))
    def merge(self, old):
        pass
    def write_defs(self, fp=sys.stdout):
        fp.write('(define-' + self.deftype + ' ' + self.name + '\n')
        if self.in_module:
            fp.write('  (in-module "' + self.in_module + '")\n')
        fp.write('  (c-name "' + self.c_name + '")\n')
        fp.write('  (gtype-id "' + self.typecode + '")\n')
        if self.values:
            fp.write('  (values\n')
            for name, val in self.values:
                fp.write('    \'("' + name + '" "' + val + '")\n')
            fp.write('  )\n')
        fp.write(')\n\n')

class FlagsDef(EnumDef):
    def __init__(self, *args):
        apply(EnumDef.__init__, (self,) + args)
        self.deftype = 'flags'

class BoxedDef(Definition):
    def __init__(self, name, *args):
        self.name = name
        self.module = None
        self.c_name = None
        self.typecode = None
        self.copy = None
        self.release = None
        self.fields = []
        for arg in get_valid_scheme_definitions(args):
            if arg[0] == 'in-module':
                self.module = arg[1]
            elif arg[0] == 'c-name':
                self.c_name = arg[1]
            elif arg[0] == 'gtype-id':
                self.typecode = arg[1]
            elif arg[0] == 'copy-func':
                self.copy = arg[1]
            elif arg[0] == 'release-func':
                self.release = arg[1]
            elif arg[0] == 'fields':
                for parg in arg[1:]:
                    self.fields.append((parg[0], parg[1]))
    def merge(self, old):
        # currently the .h parser doesn't try to work out what fields of
        # an object structure should be public, so we just copy the list
        # from the old version ...
        self.fields = old.fields
    def write_defs(self, fp=sys.stdout):
        fp.write('(define-boxed ' + self.name + '\n')
        if self.module:
            fp.write('  (in-module "' + self.module + '")\n')
        if self.c_name:
            fp.write('  (c-name "' + self.c_name + '")\n')
        if self.typecode:
            fp.write('  (gtype-id "' + self.typecode + '")\n')
        if self.copy:
            fp.write('  (copy-func "' + self.copy + '")\n')
        if self.release:
            fp.write('  (release-func "' + self.release + '")\n')
        if self.fields:
            fp.write('  (fields\n')
            for (ftype, fname) in self.fields:
                fp.write('    \'("' + ftype + '" "' + fname + '")\n')
            fp.write('  )\n')
        fp.write(')\n\n')

class PointerDef(Definition):
    def __init__(self, name, *args):
        self.name = name
        self.module = None
        self.c_name = None
        self.typecode = None
        self.fields = []
        for arg in get_valid_scheme_definitions(args):
            if arg[0] == 'in-module':
                self.module = arg[1]
            elif arg[0] == 'c-name':
                self.c_name = arg[1]
            elif arg[0] == 'gtype-id':
                self.typecode = arg[1]
            elif arg[0] == 'fields':
                for parg in arg[1:]:
                    self.fields.append((parg[0], parg[1]))
    def merge(self, old):
        # currently the .h parser doesn't try to work out what fields of
        # an object structure should be public, so we just copy the list
        # from the old version ...
        self.fields = old.fields
    def write_defs(self, fp=sys.stdout):
        fp.write('(define-pointer ' + self.name + '\n')
        if self.module:
            fp.write('  (in-module "' + self.module + '")\n')
        if self.c_name:
            fp.write('  (c-name "' + self.c_name + '")\n')
        if self.typecode:
            fp.write('  (gtype-id "' + self.typecode + '")\n')
        if self.fields:
            fp.write('  (fields\n')
            for (ftype, fname) in self.fields:
                fp.write('    \'("' + ftype + '" "' + fname + '")\n')
            fp.write('  )\n')
        fp.write(')\n\n')

class MethodDefBase(Definition):
    def __init__(self, name, *args):
        dump = 0
        self.name = name
        self.ret = None
        self.caller_owns_return = None
        self.unblock_threads = None
        self.c_name = None
        self.typecode = None
        self.of_object = None
        self.params = [] # of form (type, name, default, nullok)
        self.varargs = 0
        self.deprecated = None
        for arg in get_valid_scheme_definitions(args):
            if arg[0] == 'of-object':
                self.of_object = arg[1]
            elif arg[0] == 'docstring':
                self.docstring = make_docstring(arg[1:])
            elif arg[0] == 'c-name':
                self.c_name = arg[1]
            elif arg[0] == 'gtype-id':
                self.typecode = arg[1]
            elif arg[0] == 'return-type':
                self.ret = arg[1]
            elif arg[0] == 'caller-owns-return':
                self.caller_owns_return = arg[1] in ('t', '#t')
            elif arg[0] == 'unblock-threads':
                self.unblock_threads = arg[1] in ('t', '#t')
            elif arg[0] == 'parameters':
                for parg in arg[1:]:
                    ptype = parg[0]
                    pname = parg[1]
                    pdflt = None
                    pnull = 0
                    pdir = None
                    for farg in parg[2:]:
                        assert isinstance(farg, tuple)
                        if farg[0] == 'default':
                            pdflt = farg[1]
                        elif farg[0] == 'null-ok':
                            pnull = 1
                        elif farg[0] == 'direction':
                            pdir = farg[1]
                    self.params.append(Parameter(ptype, pname, pdflt, pnull, pdir))
            elif arg[0] == 'varargs':
                self.varargs = arg[1] in ('t', '#t')
            elif arg[0] == 'deprecated':
                self.deprecated = arg[1]
            else:
                sys.stderr.write("Warning: %s argument unsupported.\n"
                                 % (arg[0]))
                dump = 1
        if dump:
            self.write_defs(sys.stderr)

        if self.caller_owns_return is None and self.ret is not None:
            self.guess_return_value_ownership()

    def merge(self, old, parmerge):
        self.caller_owns_return = old.caller_owns_return
        self.varargs = old.varargs
        # here we merge extra parameter flags accross to the new object.
        if not parmerge:
            self.params = copy.deepcopy(old.params)
            return
        for i in range(len(self.params)):
            ptype, pname, pdflt, pnull = self.params[i]
            for p2 in old.params:
                if p2[1] == pname:
                    self.params[i] = (ptype, pname, p2[2], p2[3])
                    break
    def _write_defs(self, fp=sys.stdout):
        if self.of_object != (None, None):
            fp.write('  (of-object "' + self.of_object + '")\n')
        if self.c_name:
            fp.write('  (c-name "' + self.c_name + '")\n')
        if self.typecode:
            fp.write('  (gtype-id "' + self.typecode + '")\n')
        if self.caller_owns_return:
            fp.write('  (caller-owns-return #t)\n')
        if self.unblock_threads:
            fp.write('  (unblock_threads #t)\n')
        if self.ret:
            fp.write('  (return-type "' + self.ret + '")\n')
        if self.deprecated:
            fp.write('  (deprecated "' + self.deprecated + '")\n')
        if self.params:
            fp.write('  (parameters\n')
            for ptype, pname, pdflt, pnull in self.params:
                fp.write('    \'("' + ptype + '" "' + pname +'"')
                if pdflt: fp.write(' (default "' + pdflt + '")')
                if pnull: fp.write(' (null-ok)')
                fp.write(')\n')
            fp.write('  )\n')
        if self.varargs:
            fp.write('  (varargs #t)\n')
        fp.write(')\n\n')


class MethodDef(MethodDefBase):
    def __init__(self, name, *args):
        MethodDefBase.__init__(self, name, *args)
        for item in ('c_name', 'of_object'):
            if self.__dict__[item] == None:
                self.write_defs(sys.stderr)
                raise RuntimeError, "definition missing required %s" % (item,)

    def write_defs(self, fp=sys.stdout):
        fp.write('(define-method ' + self.name + '\n')
        self._write_defs(fp)

class VirtualDef(MethodDefBase):
    def write_defs(self, fp=sys.stdout):
        fp.write('(define-virtual ' + self.name + '\n')
        self._write_defs(fp)

class FunctionDef(Definition):
    def __init__(self, name, *args):
        dump = 0
        self.name = name
        self.in_module = None
        self.is_constructor_of = None
        self.ret = None
        self.caller_owns_return = None
        self.unblock_threads = None
        self.c_name = None
        self.typecode = None
        self.params = [] # of form (type, name, default, nullok)
        self.varargs = 0
        self.deprecated = None
        for arg in get_valid_scheme_definitions(args):
            if arg[0] == 'in-module':
                self.in_module = arg[1]
            elif arg[0] == 'docstring':
                self.docstring = make_docstring(arg[1:])
            elif arg[0] == 'is-constructor-of':
                self.is_constructor_of = arg[1]
            elif arg[0] == 'c-name':
                self.c_name = arg[1]
            elif arg[0] == 'gtype-id':
                self.typecode = arg[1]
            elif arg[0] == 'return-type':
                self.ret = arg[1]
            elif arg[0] == 'caller-owns-return':
                self.caller_owns_return = arg[1] in ('t', '#t')
            elif arg[0] == 'unblock-threads':
                self.unblock_threads = arg[1] in ('t', '#t')
            elif arg[0] == 'parameters':
                for parg in arg[1:]:
                    ptype = parg[0]
                    pname = parg[1]
                    pdflt = None
                    pnull = 0
                    for farg in parg[2:]:
                        if farg[0] == 'default':
                            pdflt = farg[1]
                        elif farg[0] == 'null-ok':
                            pnull = 1
                    self.params.append(Parameter(ptype, pname, pdflt, pnull))
            elif arg[0] == 'properties':
                if self.is_constructor_of is None:
                    print >> sys.stderr, "Warning: (properties ...) "\
                          "is only valid for constructors"
                for prop in arg[1:]:
                    pname = prop[0]
                    optional = False
                    argname = pname
                    for farg in prop[1:]:
                        if farg[0] == 'optional':
                            optional = True
                        elif farg[0] == 'argname':
                            argname = farg[1]
                    self.params.append(Property(pname, optional, argname))
            elif arg[0] == 'varargs':
                self.varargs = arg[1] in ('t', '#t')
            elif arg[0] == 'deprecated':
                self.deprecated = arg[1]
            else:
                sys.stderr.write("Warning: %s argument unsupported\n"
                                 % (arg[0],))
                dump = 1
        if dump:
            self.write_defs(sys.stderr)

        if self.caller_owns_return is None and self.ret is not None:
            self.guess_return_value_ownership()
        for item in ('c_name',):
            if self.__dict__[item] == None:
                self.write_defs(sys.stderr)
                raise RuntimeError, "definition missing required %s" % (item,)

    _method_write_defs = MethodDef.__dict__['write_defs']

    def merge(self, old, parmerge):
        self.caller_owns_return = old.caller_owns_return
        self.varargs = old.varargs
        if not parmerge:
            self.params = copy.deepcopy(old.params)
            return
        # here we merge extra parameter flags accross to the new object.
        def merge_param(param):
            for old_param in old.params:
                if old_param.pname == param.pname:
                    if isinstance(old_param, Property):
                        # h2def never scans Property's, therefore if
                        # we have one it was manually written, so we
                        # keep it.
                        return copy.deepcopy(old_param)
                    else:
                        param.merge(old_param)
                        return param
            raise RuntimeError, "could not find %s in old_parameters %r" % (
                param.pname, [p.pname for p in old.params])
        try:
            self.params = map(merge_param, self.params)
        except RuntimeError:
            # parameter names changed and we can't find a match; it's
            # safer to keep the old parameter list untouched.
            self.params = copy.deepcopy(old.params)

        if not self.is_constructor_of:
            try:
                self.is_constructor_of = old.is_constructor_of
            except AttributeError:
                pass
        if isinstance(old, MethodDef):
            self.name = old.name
            # transmogrify from function into method ...
            self.write_defs = self._method_write_defs
            self.of_object = old.of_object
            del self.params[0]
    def write_defs(self, fp=sys.stdout):
        fp.write('(define-function ' + self.name + '\n')
        if self.in_module:
            fp.write('  (in-module "' + self.in_module + '")\n')
        if self.is_constructor_of:
            fp.write('  (is-constructor-of "' + self.is_constructor_of +'")\n')
        if self.c_name:
            fp.write('  (c-name "' + self.c_name + '")\n')
        if self.typecode:
            fp.write('  (gtype-id "' + self.typecode + '")\n')
        if self.caller_owns_return:
            fp.write('  (caller-owns-return #t)\n')
        if self.unblock_threads:
            fp.write('  (unblock-threads #t)\n')
        if self.ret:
            fp.write('  (return-type "' + self.ret + '")\n')
        if self.deprecated:
            fp.write('  (deprecated "' + self.deprecated + '")\n')
        if self.params:
            if isinstance(self.params[0], Parameter):
                fp.write('  (parameters\n')
                for ptype, pname, pdflt, pnull in self.params:
                    fp.write('    \'("' + ptype + '" "' + pname +'"')
                    if pdflt: fp.write(' (default "' + pdflt + '")')
                    if pnull: fp.write(' (null-ok)')
                    fp.write(')\n')
                fp.write('  )\n')
            elif isinstance(self.params[0], Property):
                fp.write('  (properties\n')
                for prop in self.params:
                    fp.write('    \'("' + prop.pname +'"')
                    if prop.optional: fp.write(' (optional)')
                    fp.write(')\n')
                fp.write('  )\n')
            else:
                assert False, "strange parameter list %r" % self.params[0]
        if self.varargs:
            fp.write('  (varargs #t)\n')

        fp.write(')\n\n')
