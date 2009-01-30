### -*- python -*-
### Code to generate "Reverse Wrappers", i.e. C->Python wrappers
### (C) 2004 Gustavo Carneiro <gjc@gnome.org>
import argtypes
import os

DEBUG_MODE = ('PYGTK_CODEGEN_DEBUG' in os.environ)

def join_ctype_name(ctype, name):
    '''Joins a C type and a variable name into a single string'''
    if ctype[-1] != '*':
        return " ".join((ctype, name))
    else:
        return "".join((ctype, name))


class CodeSink(object):
    def __init__(self):
        self.indent_level = 0 # current indent level
        self.indent_stack = [] # previous indent levels

    def _format_code(self, code):
        assert isinstance(code, str)
        l = []
        for line in code.split('\n'):
            l.append(' '*self.indent_level + line)
        if l[-1]:
            l.append('')
        return '\n'.join(l)

    def writeln(self, line=''):
        raise NotImplementedError

    def indent(self, level=4):
        '''Add a certain ammount of indentation to all lines written
        from now on and until unindent() is called'''
        self.indent_stack.append(self.indent_level)
        self.indent_level += level

    def unindent(self):
        '''Revert indentation level to the value before last indent() call'''
        self.indent_level = self.indent_stack.pop()


class FileCodeSink(CodeSink):
    def __init__(self, fp):
        CodeSink.__init__(self)
        assert isinstance(fp, file)
        self.fp = fp

    def writeln(self, line=''):
        self.fp.write(self._format_code(line))

class MemoryCodeSink(CodeSink):
    def __init__(self):
        CodeSink.__init__(self)
        self.lines = []

    def writeln(self, line=''):
        self.lines.append(self._format_code(line))

    def flush_to(self, sink):
        assert isinstance(sink, CodeSink)
        for line in self.lines:
            sink.writeln(line.rstrip())
        self.lines = []

    def flush(self):
        l = []
        for line in self.lines:
            l.append(self._format_code(line))
        self.lines = []
        return "".join(l)

class ReverseWrapper(object):
    '''Object that generates a C->Python wrapper'''
    def __init__(self, cname, is_static=True):
        assert isinstance(cname, str)

        self.cname = cname
        ## function object we will call, or object whose method we will call
        self.called_pyobj = None
        ## name of method of self.called_pyobj we will call
        self.method_name = None
        self.is_static = is_static

        self.parameters = []
        self.declarations = MemoryCodeSink()
        self.post_return_code = MemoryCodeSink()
        self.body = MemoryCodeSink()
        self.check_exception_code = MemoryCodeSink()
        self.cleanup_actions = []
        self.pyargv_items = []
        self.pyargv_optional_items = []
        self.pyret_parse_items = [] # list of (format_spec, parameter)
        self.code_sinks_stack = [self.body]

    def set_call_target(self, called_pyobj, method_name=None):
        assert called_pyobj is not None
        assert self.called_pyobj is None
        self.called_pyobj = called_pyobj
        self.method_name = method_name

    def set_return_type(self, return_type):
        assert isinstance(return_type, ReturnType)
        self.return_type = return_type

    def add_parameter(self, param):
        assert isinstance(param, Parameter)
        self.parameters.append(param)

    def add_declaration(self, decl_code):
        self.declarations.writeln(decl_code)

    def add_pyargv_item(self, variable, optional=False):
        if optional:
            self.pyargv_optional_items.append(variable)
        else:
            self.pyargv_items.append(variable)

    def add_pyret_parse_item(self, format_specifier, parameter, prepend=False):
        if prepend:
            self.pyret_parse_items.insert(0, (format_specifier, parameter))
        else:
            self.pyret_parse_items.append((format_specifier, parameter))


    def push_code_sink(self, code_sink):
        self.code_sinks_stack.insert(0, code_sink)

    def pop_code_sink(self):
        return self.code_sinks_stack.pop(0)


    def write_code(self, code,
                   cleanup=None,
                   failure_expression=None,
                   failure_cleanup=None,
                   failure_exception=None,
                   code_sink=None):
        '''Add a chunk of code with cleanup and error handling

        This method is to be used by TypeHandlers when generating code

        Keywork arguments:
        code -- code to add
        cleanup -- code to cleanup any dynamic resources created by @code
                   (except in case of failure) (default None)
        failure_expression -- C boolean expression to indicate
                              if anything failed (default None)
        failure_cleanup -- code to cleanup any dynamic resources
                           created by @code in case of failure (default None)
        failure_exception -- code to raise an exception in case of
                             failure (which will be immediately
                             printed and cleared), (default None)
        code_sink -- "code sink" to use; by default,
                      ReverseWrapper.body is used, which writes the
                      main body of the wrapper, before calling the
                      python method.  Alternatively,
                      ReverseWrapper.after_pyret_parse can be used, to
                      write code after the PyArg_ParseTuple that
                      parses the python method return value.
        '''
        if code_sink is None:
            code_sink = self.code_sinks_stack[0]
        if code is not None:
            code_sink.writeln(code)
        if failure_expression is not None:
            code_sink.writeln("if (%s) {" % (failure_expression,))
            code_sink.indent()
            if failure_exception is None:
                code_sink.writeln("if (PyErr_Occurred())")
                code_sink.indent()
                code_sink.writeln("PyErr_Print();")
                code_sink.unindent()
            else:
                code_sink.writeln(failure_exception)
                code_sink.writeln("PyErr_Print();")
            if failure_cleanup is not None:
                code_sink.writeln(failure_cleanup)
            for cleanup_action in self.cleanup_actions:
                code_sink.writeln(cleanup_action)

            self.push_code_sink(code_sink)
            try:
                self.return_type.write_error_return()
            finally:
                self.pop_code_sink()

            code_sink.unindent()
            code_sink.writeln("}")
        if cleanup is not None:
            self.cleanup_actions.insert(0, cleanup)

    def generate(self, sink):
        '''Generate the code into a CodeSink object'''
        assert isinstance(sink, CodeSink)

        if DEBUG_MODE:
            self.declarations.writeln("/* begin declarations */")
            self.body.writeln("/* begin main body */")
            self.post_return_code.writeln("/* begin post-return code */")

        self.add_declaration("PyGILState_STATE __py_state;")
        self.write_code(code="__py_state = pyg_gil_state_ensure();",
                        cleanup="pyg_gil_state_release(__py_state);")

        for param in self.parameters:
            param.convert_c2py()

        assert self.called_pyobj is not None,\
               "Parameters failed to provide a target function or method."

        if self.is_static:
            sink.writeln('static %s' % self.return_type.get_c_type())
        else:
            sink.writeln(self.return_type.get_c_type())
        c_proto_params = map(Parameter.format_for_c_proto, self.parameters)
        sink.writeln("%s(%s)\n{" % (self.cname, ", ".join(c_proto_params)))

        self.return_type.write_decl()
        self.add_declaration("PyObject *py_retval;")

        ## Handle number of arguments
        if self.pyargv_items:
            self.add_declaration("PyObject *py_args;")
            py_args = "py_args"
            if self.pyargv_optional_items:
                self.add_declaration("int argc = %i;" % len(self.pyargv_items))
                argc = "argc"
                for arg in self.pyargv_optional_items:
                    self.body.writeln("if (%s)" % arg)
                    self.body.indent()
                    self.body.writeln("++argc;")
                    self.body.unindent()
            else:
                argc = str(len(self.pyargv_items))
        else:
            if self.pyargv_optional_items:
                self.add_declaration("PyObject *py_args;")
                py_args = "py_args"
                self.add_declaration("int argc = 0;")
                argc = "argc"
                for arg in self.pyargv_optional_items:
                    self.body.writeln("if (%s)" % arg)
                    self.body.indent()
                    self.body.writeln("++argc;")
                    self.body.unindent()
            else:
                py_args = "NULL"
                argc = None

        self.body.writeln()

        if py_args != "NULL":
            self.write_code("py_args = PyTuple_New(%s);" % argc,
                            cleanup="Py_DECREF(py_args);")
            pos = 0
            for arg in self.pyargv_items:
                try: # try to remove the Py_DECREF cleanup action, if we can
                    self.cleanup_actions.remove("Py_DECREF(%s);" % arg)
                except ValueError: # otherwise we have to Py_INCREF..
                    self.body.writeln("Py_INCREF(%s);" % arg)
                self.body.writeln("PyTuple_SET_ITEM(%s, %i, %s);" % (py_args, pos, arg))
                pos += 1
            for arg in self.pyargv_optional_items:
                self.body.writeln("if (%s) {" % arg)
                self.body.indent()
                try: # try to remove the Py_DECREF cleanup action, if we can
                    self.cleanup_actions.remove("Py_XDECREF(%s);" % arg)
                except ValueError: # otherwise we have to Py_INCREF..
                    self.body.writeln("Py_INCREF(%s);" % arg)
                self.body.writeln("PyTuple_SET_ITEM(%s, %i, %s);" % (py_args, pos, arg))
                self.body.unindent()
                self.body.writeln("}")
                pos += 1

        self.body.writeln()

        ## Call the python method
        if self.method_name is None:
            self.write_code("py_retval = PyObject_Call(%s, %s);"
                            % (self.called_pyobj, py_args),
                            cleanup="Py_XDECREF(py_retval);")
            self.check_exception_code.flush_to(self.body)
            self.write_code(None, failure_expression="!py_retval")

        else:
            self.add_declaration("PyObject *py_method;")
            self.write_code("py_method = PyObject_GetAttrString(%s, \"%s\");"
                            % (self.called_pyobj, self.method_name),
                            cleanup="Py_DECREF(py_method);",
                            failure_expression="!py_method")
            self.write_code("py_retval = PyObject_CallObject(py_method, %s);"
                            % (py_args,),
                            cleanup="Py_XDECREF(py_retval);")
            self.check_exception_code.flush_to(self.body)
            self.write_code(None, failure_expression="!py_retval")

        ## -- Handle the return value --

        ## we need to check if the return_type object is prepared to cooperate with multiple return values
        len_before = len(self.pyret_parse_items)
        self.return_type.write_conversion()
        len_after = len(self.pyret_parse_items)
        assert (self.return_type.get_c_type() == 'void'
                or not (len_before == len_after and len_after > 0)),\
               ("Bug in reverse wrappers: return type handler %s"
                " is not prepared to cooperate multiple return values") % (type(self.return_type),)

        sink.indent()

        if self.pyret_parse_items == [("", "")]:
            ## special case when there are no return parameters
            self.write_code(
                code=None,
                failure_expression='py_retval != Py_None',
                failure_exception=('PyErr_SetString(PyExc_TypeError, '
                                   '"virtual method should return None");'))
        else:    
            if len(self.pyret_parse_items) == 1:
                ## if retval is one item only, pack it in a tuple so we
                ## can use PyArg_ParseTuple as usual..
                self.write_code('py_retval = Py_BuildValue("(N)", py_retval);')
            if len(self.pyret_parse_items) > 0:
                ## Parse return values using PyArg_ParseTuple
                params = ["py_retval",
                          '"%s"' % "".join([format for format, param in self.pyret_parse_items])]
                params.extend([param for format, param in self.pyret_parse_items if param])
                self.write_code(code=None, failure_expression=(
                    '!PyArg_ParseTuple(%s)' % (', '.join(params),)))

        if DEBUG_MODE:
            self.declarations.writeln("/* end declarations */")
        self.declarations.flush_to(sink)
        sink.writeln()
        if DEBUG_MODE:
            self.body.writeln("/* end main body */")
        self.body.flush_to(sink)
        sink.writeln()
        if DEBUG_MODE:
            self.post_return_code.writeln("/* end post-return code */")
        self.post_return_code.flush_to(sink)
        sink.writeln()

        for cleanup_action in self.cleanup_actions:
            sink.writeln(cleanup_action)
        if self.return_type.get_c_type() != 'void':
            sink.writeln()
            sink.writeln("return retval;")
        sink.unindent()
        sink.writeln("}")

class TypeHandler(object):
    def __init__(self, wrapper, **props):
        assert isinstance(wrapper, ReverseWrapper)
        self.wrapper = wrapper
        self.props = props

class ReturnType(TypeHandler):

    def get_c_type(self):
        raise NotImplementedError

    def write_decl(self):
        raise NotImplementedError

    def write_error_return(self):
        '''Write "return <value>" code in case of error'''
        raise NotImplementedError

    def write_conversion(self):
        '''Writes code to convert Python return value in 'py_retval'
        into C 'retval'.  Returns a string with C boolean expression
        that determines if anything went wrong. '''
        raise NotImplementedError

class Parameter(TypeHandler):

    def __init__(self, wrapper, name, **props):
        TypeHandler.__init__(self, wrapper, **props)
        self.name = name

    def get_c_type(self):
        raise NotImplementedError

    def convert_c2py(self):
        '''Write some code before calling the Python method.'''
        pass

    def format_for_c_proto(self):
        return join_ctype_name(self.get_c_type(), self.name)


###---
class StringParam(Parameter):

    def get_c_type(self):
        return self.props.get('c_type', 'char *').replace('const-', 'const ')

    def convert_c2py(self):
        if self.props.get('optional', False):
            self.wrapper.add_declaration("PyObject *py_%s = NULL;" % self.name)
            self.wrapper.write_code(code=("if (%s)\n"
                                          "    py_%s = PyString_FromString(%s);\n"
                                          % (self.name, self.name, self.name)),
                                    cleanup=("Py_XDECREF(py_%s);" % self.name))
            self.wrapper.add_pyargv_item("py_%s" % self.name, optional=True)
        else:
            self.wrapper.add_declaration("PyObject *py_%s;" % self.name)
            self.wrapper.write_code(code=("py_%s = PyString_FromString(%s);" %
                                          (self.name, self.name)),
                                    cleanup=("Py_DECREF(py_%s);" % self.name),
                                    failure_expression=("!py_%s" % self.name))
            self.wrapper.add_pyargv_item("py_%s" % self.name)

for ctype in ('char*', 'gchar*', 'const-char*', 'char-const*', 'const-gchar*',
              'gchar-const*', 'string', 'static_string'):
    argtypes.matcher.register_reverse(ctype, StringParam)
del ctype

class StringReturn(ReturnType):

    def get_c_type(self):
        return self.props.get('c_type', 'char *').replace('const-', 'const ')
    #return "char *"

    def write_decl(self):
        self.wrapper.add_declaration("%s retval;" % self.get_c_type())
        #self.wrapper.add_declaration("char *retval;")

    def write_error_return(self):
        self.wrapper.write_code("return NULL;")

    def write_conversion(self):
        self.wrapper.add_pyret_parse_item("s", "&retval", prepend=True)
        self.wrapper.write_code("retval = g_strdup(retval);", code_sink=self.wrapper.post_return_code)

for ctype in ('char*', 'gchar*', 'const-gchar*'):
    argtypes.matcher.register_reverse_ret(ctype, StringReturn)
del ctype


class VoidReturn(ReturnType):

    def get_c_type(self):
        return "void"

    def write_decl(self):
        pass

    def write_error_return(self):
        self.wrapper.write_code("return;")

    def write_conversion(self):
        self.wrapper.add_pyret_parse_item("", "", prepend=True)

argtypes.matcher.register_reverse_ret('void', VoidReturn)
argtypes.matcher.register_reverse_ret('none', VoidReturn)

class GObjectParam(Parameter):

    def get_c_type(self):
        return self.props.get('c_type', 'GObject *')

    def convert_c2py(self):
        self.wrapper.add_declaration("PyObject *py_%s = NULL;" % self.name)
        self.wrapper.write_code(code=("if (%s)\n"
                                      "    py_%s = pygobject_new((GObject *) %s);\n"
                                      "else {\n"
                                      "    Py_INCREF(Py_None);\n"
                                      "    py_%s = Py_None;\n"
                                      "}"
                                      % (self.name, self.name, self.name, self.name)),
                                cleanup=("Py_DECREF(py_%s);" % self.name))
        self.wrapper.add_pyargv_item("py_%s" % self.name)

argtypes.matcher.register_reverse('GObject*', GObjectParam)

class GObjectReturn(ReturnType):

    def get_c_type(self):
        return self.props.get('c_type', 'GObject *')

    def write_decl(self):
        self.wrapper.add_declaration("%s retval;" % self.get_c_type())

    def write_error_return(self):
        self.wrapper.write_code("return NULL;")

    def write_conversion(self):
        self.wrapper.write_code(
            code=None,
            failure_expression="!PyObject_TypeCheck(py_retval, &PyGObject_Type)",
            failure_exception='PyErr_SetString(PyExc_TypeError, "retval should be a GObject");')
        self.wrapper.write_code("retval = (%s) pygobject_get(py_retval);"
                                % self.get_c_type())
        self.wrapper.write_code("g_object_ref((GObject *) retval);")

argtypes.matcher.register_reverse_ret('GObject*', GObjectReturn)



class IntParam(Parameter):

    def get_c_type(self):
        return self.props.get('c_type', 'int')

    def convert_c2py(self):
        self.wrapper.add_declaration("PyObject *py_%s;" % self.name)
        self.wrapper.write_code(code=("py_%s = PyInt_FromLong(%s);" %
                                      (self.name, self.name)),
                                cleanup=("Py_DECREF(py_%s);" % self.name))
        self.wrapper.add_pyargv_item("py_%s" % self.name)

class IntReturn(ReturnType):
    def get_c_type(self):
        return self.props.get('c_type', 'int')
    def write_decl(self):
        self.wrapper.add_declaration("%s retval;" % self.get_c_type())
    def write_error_return(self):
        self.wrapper.write_code("return -G_MAXINT;")
    def write_conversion(self):
        self.wrapper.add_pyret_parse_item("i", "&retval", prepend=True)

for argtype in ('int', 'gint', 'guint', 'short', 'gshort', 'gushort', 'long',
                'glong', 'gsize', 'gssize', 'guint8', 'gint8', 'guint16',
                'gint16', 'gint32', 'GTime'):
    argtypes.matcher.register_reverse(argtype, IntParam)
    argtypes.matcher.register_reverse_ret(argtype, IntReturn)
del argtype

class IntPtrParam(Parameter):
    def __init__(self, wrapper, name, **props):
        if "direction" not in props:
            raise argtypes.ArgTypeConfigurationError(
                "cannot use int* parameter without direction")
        if props["direction"] not in ("out", "inout"):
            raise argtypes.ArgTypeConfigurationError(
                "cannot use int* parameter with direction '%s'"
                % (props["direction"],))
        Parameter.__init__(self, wrapper, name, **props)
    def get_c_type(self):
        return self.props.get('c_type', 'int*')
    def convert_c2py(self):
        if self.props["direction"] == "inout":
            self.wrapper.add_declaration("PyObject *py_%s;" % self.name)
            self.wrapper.write_code(code=("py_%s = PyInt_FromLong(*%s);" %
                                          (self.name, self.name)),
                                    cleanup=("Py_DECREF(py_%s);" % self.name))
            self.wrapper.add_pyargv_item("py_%s" % self.name)
        self.wrapper.add_pyret_parse_item("i", self.name)
for argtype in ('int*', 'gint*'):
    argtypes.matcher.register_reverse(argtype, IntPtrParam)
del argtype


class GEnumReturn(IntReturn):
    def write_conversion(self):
        self.wrapper.write_code(
            code=None,
            failure_expression=(
            "pyg_enum_get_value(%s, py_retval, (gint *)&retval)"
            % (self.props['typecode'],)))

argtypes.matcher.register_reverse_ret("GEnum", GEnumReturn)

class GEnumParam(IntParam):
    def convert_c2py(self):
        self.wrapper.add_declaration("PyObject *py_%s;" % self.name)
        self.wrapper.write_code(code=("py_%s = pyg_enum_from_gtype(%s, %s);" %
                                (self.name, self.props['typecode'], self.name)),
                        cleanup=("Py_DECREF(py_%s);" % self.name),
                        failure_expression=("!py_%s" % self.name))
        self.wrapper.add_pyargv_item("py_%s" % self.name)

argtypes.matcher.register_reverse("GEnum", GEnumParam)

class GFlagsReturn(IntReturn):
    def write_conversion(self):
        self.wrapper.write_code(
            code=None,
            failure_expression=(
            "pyg_flags_get_value(%s, py_retval, (gint *)&retval)" %
            self.props['typecode']))

argtypes.matcher.register_reverse_ret("GFlags", GFlagsReturn)

class GFlagsParam(IntParam):
    def convert_c2py(self):
        self.wrapper.add_declaration("PyObject *py_%s;" % self.name)
        self.wrapper.write_code(code=(
            "py_%s = pyg_flags_from_gtype(%s, %s);" %
            (self.name, self.props['typecode'], self.name)),
                                cleanup=("Py_DECREF(py_%s);" % self.name),
                                failure_expression=("!py_%s" % self.name))
        self.wrapper.add_pyargv_item("py_%s" % self.name)

argtypes.matcher.register_reverse("GFlags", GFlagsParam)


class GtkTreePathParam(IntParam):
    def convert_c2py(self):
        self.wrapper.add_declaration("PyObject *py_%s;" % self.name)
        self.wrapper.write_code(code=(
            "py_%s = pygtk_tree_path_to_pyobject(%s);" %
            (self.name, self.name)),
                                cleanup=("Py_DECREF(py_%s);" % self.name),
                                failure_expression=("!py_%s" % self.name))
        self.wrapper.add_pyargv_item("py_%s" % self.name)

argtypes.matcher.register_reverse("GtkTreePath*", GtkTreePathParam)


class GtkTreePathReturn(ReturnType):
    def get_c_type(self):
        return self.props.get('c_type', 'GtkTreePath *')
    def write_decl(self):
        self.wrapper.add_declaration("GtkTreePath * retval;")
    def write_error_return(self):
        self.wrapper.write_code("return NULL;")
    def write_conversion(self):
        self.wrapper.write_code(
            "retval = pygtk_tree_path_from_pyobject(py_retval);\n",
            failure_expression=('!retval'),
            failure_exception=(
    'PyErr_SetString(PyExc_TypeError, "retval should be a GtkTreePath");'))

argtypes.matcher.register_reverse_ret("GtkTreePath*", GtkTreePathReturn)


class BooleanReturn(ReturnType):
    def get_c_type(self):
        return "gboolean"
    def write_decl(self):
        self.wrapper.add_declaration("gboolean retval;")
        self.wrapper.add_declaration("PyObject *py_main_retval;")
    def write_error_return(self):
        self.wrapper.write_code("return FALSE;")
    def write_conversion(self):
        self.wrapper.add_pyret_parse_item("O", "&py_main_retval", prepend=True)
        self.wrapper.write_code(
            "retval = PyObject_IsTrue(py_main_retval)? TRUE : FALSE;",
            code_sink=self.wrapper.post_return_code)
argtypes.matcher.register_reverse_ret("gboolean", BooleanReturn)

class BooleanParam(Parameter):
    def get_c_type(self):
        return "gboolean"
    def convert_c2py(self):
        self.wrapper.add_declaration("PyObject *py_%s;" % self.name)
        self.wrapper.write_code("py_%s = %s? Py_True : Py_False;"
                                % (self.name, self.name))
        self.wrapper.add_pyargv_item("py_%s" % self.name)

argtypes.matcher.register_reverse("gboolean", BooleanParam)


class DoubleParam(Parameter):
    def get_c_type(self):
        return self.props.get('c_type', 'gdouble')
    def convert_c2py(self):
        self.wrapper.add_declaration("PyObject *py_%s;" % self.name)
        self.wrapper.write_code(code=("py_%s = PyFloat_FromDouble(%s);" %
                                      (self.name, self.name)),
                                cleanup=("Py_DECREF(py_%s);" % self.name))
        self.wrapper.add_pyargv_item("py_%s" % self.name)

class DoublePtrParam(Parameter):
    def __init__(self, wrapper, name, **props):
        if "direction" not in props:
            raise argtypes.ArgTypeConfigurationError(
                "cannot use double* parameter without direction")
        if props["direction"] not in ("out", ): # inout not yet implemented
            raise argtypes.ArgTypeConfigurationError(
                "cannot use double* parameter with direction '%s'"
                % (props["direction"],))
        Parameter.__init__(self, wrapper, name, **props)
    def get_c_type(self):
        return self.props.get('c_type', 'double*')
    def convert_c2py(self):
        self.wrapper.add_pyret_parse_item("d", self.name)
for argtype in ('double*', 'gdouble*'):
    argtypes.matcher.register_reverse(argtype, DoublePtrParam)
del argtype

class DoubleReturn(ReturnType):
    def get_c_type(self):
        return self.props.get('c_type', 'gdouble')
    def write_decl(self):
        self.wrapper.add_declaration("%s retval;" % self.get_c_type())
    def write_error_return(self):
        self.wrapper.write_code("return -G_MAXFLOAT;")
    def write_conversion(self):
        self.wrapper.add_pyret_parse_item("d", "&retval", prepend=True)

for argtype in ('float', 'double', 'gfloat', 'gdouble'):
    argtypes.matcher.register_reverse(argtype, DoubleParam)
    argtypes.matcher.register_reverse_ret(argtype, DoubleReturn)


class GBoxedParam(Parameter):
    def get_c_type(self):
        return self.props.get('c_type').replace('const-', 'const ')
    def convert_c2py(self):
        self.wrapper.add_declaration("PyObject *py_%s;" % self.name)
        ctype = self.get_c_type()
        if ctype.startswith('const '):
            ctype_no_const = ctype[len('const '):]
            self.wrapper.write_code(
                code=('py_%s = pyg_boxed_new(%s, (%s) %s, TRUE, TRUE);' %
                      (self.name, self.props['typecode'],
                       ctype_no_const, self.name)),
                cleanup=("Py_DECREF(py_%s);" % self.name))
        else:
            self.wrapper.write_code(
                code=('py_%s = pyg_boxed_new(%s, %s, FALSE, FALSE);' %
                      (self.name, self.props['typecode'], self.name)),
                cleanup=("Py_DECREF(py_%s);" % self.name))
        self.wrapper.add_pyargv_item("py_%s" % self.name)

argtypes.matcher.register_reverse("GBoxed", GBoxedParam)


class GBoxedReturn(ReturnType):
    def get_c_type(self):
        return self.props.get('c_type')
    def write_decl(self):
        self.wrapper.add_declaration("%s retval;" % self.get_c_type())
    def write_error_return(self):
        self.wrapper.write_code("return retval;")
    def write_conversion(self):
        self.wrapper.write_code(code = None,
            failure_expression=("!pyg_boxed_check(py_retval, %s)" %
                                (self.props['typecode'],)),
            failure_exception=(
            'PyErr_SetString(PyExc_TypeError, "retval should be a %s");'
            % (self.props['typename'],)))
        self.wrapper.write_code('retval = pyg_boxed_get(py_retval, %s);' %
                                self.props['typename'])

argtypes.matcher.register_reverse_ret("GBoxed", GBoxedReturn)


class GdkRegionPtrReturn(GBoxedReturn):
    def write_error_return(self):
        self.wrapper.write_code("return gdk_region_new();")
    def write_conversion(self):
        self.props['typecode'] = 'PYGDK_TYPE_REGION'
        self.props['typename'] = 'GdkRegion'
        super(GdkRegionPtrReturn, self).write_conversion()

argtypes.matcher.register_reverse_ret("GdkRegion*", GdkRegionPtrReturn)


class PangoFontDescriptionReturn(GBoxedReturn):
    def write_error_return(self):
        self.wrapper.write_code("return pango_font_description_new();")
    def write_conversion(self):
        self.props['typecode'] = 'PANGO_TYPE_FONT_DESCRIPTION'
        self.props['typename'] = 'PangoFontDescription'
        super(PangoFontDescriptionReturn, self).write_conversion()

argtypes.matcher.register_reverse_ret("PangoFontDescription*",
                                      PangoFontDescriptionReturn)


class PangoFontMetricsReturn(GBoxedReturn):
    def write_error_return(self):
        self.wrapper.write_code("return pango_font_metrics_new();")
    def write_conversion(self):
        self.props['typecode'] = 'PANGO_TYPE_FONT_METRICS'
        self.props['typename'] = 'PangoFontMetrics'
        super(PangoFontMetricsReturn, self).write_conversion()

argtypes.matcher.register_reverse_ret("PangoFontMetrics*",
                                      PangoFontMetricsReturn)


class PangoLanguageReturn(GBoxedReturn):
    def write_error_return(self):
        self.wrapper.write_code("return pango_language_from_string(\"\");")
    def write_conversion(self):
        self.props['typecode'] = 'PANGO_TYPE_LANGUAGE'
        self.props['typename'] = 'PangoLanguage'
        super(PangoLanguageReturn, self).write_conversion()

argtypes.matcher.register_reverse_ret("PangoLanguage*", PangoLanguageReturn)


class GdkRectanglePtrParam(Parameter):
    def get_c_type(self):
        return self.props.get('c_type').replace('const-', 'const ')
    def convert_c2py(self):
        self.wrapper.add_declaration("PyObject *py_%s;" % self.name)
        self.wrapper.write_code(
            code=('py_%s = pyg_boxed_new(GDK_TYPE_RECTANGLE, %s, TRUE, TRUE);' %
                  (self.name, self.name)),
            cleanup=("Py_DECREF(py_%s);" % self.name))
        self.wrapper.add_pyargv_item("py_%s" % self.name)

argtypes.matcher.register_reverse("GdkRectangle*", GdkRectanglePtrParam)
argtypes.matcher.register_reverse('GtkAllocation*', GdkRectanglePtrParam)


class GErrorParam(Parameter):
    def get_c_type(self):
        return self.props.get('c_type').replace('**', ' **')
    def convert_c2py(self):
        self.wrapper.write_code(code=None,
            failure_expression=("pyg_gerror_exception_check(%s)" % self.name),
                                code_sink=self.wrapper.check_exception_code)

argtypes.matcher.register_reverse('GError**', GErrorParam)


class PyGObjectMethodParam(Parameter):
    def __init__(self, wrapper, name, method_name, **props):
        Parameter.__init__(self, wrapper, name, **props)
        self.method_name = method_name

    def get_c_type(self):
        return self.props.get('c_type', 'GObject *')

    def convert_c2py(self):
        self.wrapper.add_declaration("PyObject *py_%s;" % self.name)
        self.wrapper.write_code(code=("py_%s = pygobject_new((GObject *) %s);" %
                                      (self.name, self.name)),
                                cleanup=("Py_DECREF(py_%s);" % self.name),
                                failure_expression=("!py_%s" % self.name))
        self.wrapper.set_call_target("py_%s" % self.name, self.method_name)


class CallbackInUserDataParam(Parameter):
    def __init__(self, wrapper, name, free_it, **props):
        Parameter.__init__(self, wrapper, name, **props)
        self.free_it = free_it

    def get_c_type(self):
        return "gpointer"

    def convert_c2py(self):
        self.wrapper.add_declaration("PyObject **_user_data;")
        cleanup = self.free_it and ("g_free(%s);" % self.name) or None
        self.wrapper.write_code(code=("_real_user_data = (PyObject **) %s;"
                                      % self.name),
                                cleanup=cleanup)

        self.wrapper.add_declaration("PyObject *py_func;")
        cleanup = self.free_it and "Py_DECREF(py_func);" or None
        self.wrapper.write_code(code="py_func = _user_data[0];",
                                cleanup=cleanup)
        self.wrapper.set_call_target("py_func")

        self.wrapper.add_declaration("PyObject *py_user_data;")
        cleanup = self.free_it and "Py_XDECREF(py_user_data);" or None
        self.wrapper.write_code(code="py_user_data = _user_data[1];",
                                cleanup=cleanup)
        self.wrapper.add_pyargv_item("py_user_data", optional=True)

def _test():
    import sys

    if 1:
        wrapper = ReverseWrapper("this_is_the_c_function_name", is_static=True)
        wrapper.set_return_type(StringReturn(wrapper))
        wrapper.add_parameter(PyGObjectMethodParam(wrapper, "self", method_name="do_xxx"))
        wrapper.add_parameter(StringParam(wrapper, "param2", optional=True))
        wrapper.add_parameter(GObjectParam(wrapper, "param3"))
        #wrapper.add_parameter(InoutIntParam(wrapper, "param4"))
        wrapper.generate(FileCodeSink(sys.stderr))

    if 0:
        wrapper = ReverseWrapper("this_a_callback_wrapper")
        wrapper.set_return_type(VoidReturn(wrapper))
        wrapper.add_parameter(StringParam(wrapper, "param1", optional=False))
        wrapper.add_parameter(GObjectParam(wrapper, "param2"))
        wrapper.add_parameter(CallbackInUserDataParam(wrapper, "data", free_it=True))
        wrapper.generate(FileCodeSink(sys.stderr))

if __name__ == '__main__':
    _test()
