#!/usr/bin/env python
# -*- Mode: Python; py-indent-offset: 4 -*-

import sys, os, getopt

module_init_template = \
'/* -*- Mode: C; c-basic-offset: 4 -*- */\n' + \
'#ifdef HAVE_CONFIG_H\n' + \
'#  include "config.h"\n' + \
'#endif\n' + \
'#include <Python.h>\n' + \
'#include <pygtk.h>\n' + \
'\n' + \
'/* include any extra headers needed here */\n' + \
'\n' + \
'void %(prefix)s_register_classes(PyObject *d);\n' + \
'extern PyMethodDef %(prefix)s_functions[];\n' + \
'\n' + \
'DL_EXPORT(void)\n' + \
'init%(module)s(void)\n' + \
'{\n' + \
'    PyObject *m, *d;\n' + \
'\n' + \
'    /* perform any initialisation required by the library here */\n' + \
'\n' + \
'    m = Py_InitModule("%(module)s", %(prefix)s_functions);\n' + \
'    d = PyModule_GetDict(m);\n' + \
'\n' + \
'    init_pygtk();\n' + \
'\n' + \
'    %(prefix)s_register_classes(d);\n' + \
'\n' + \
'    /* add anything else to the module dictionary (such as constants) */\n' +\
'\n' + \
'    if (PyErr_Occurred())\n' + \
'        Py_FatalError("could not initialise module %(module)s");\n' + \
'}\n'

override_template = \
'/* -*- Mode: C; c-basic-offset: 4 -*- */\n' + \
'%%%%\n' + \
'headers\n' + \
'/* include any required headers here */\n' + \
'%%%%\n' + \
'init\n' + \
'    /* include any code here that needs to be executed before the\n' + \
'     * extension classes get initialised */\n' + \
'%%%%\n' + \
'\n' + \
'/* you should add appropriate ignore, ignore-glob and\n' + \
' * override sections here */\n'

def open_with_backup(file):
    if os.path.exists(file):
        try:
            os.rename(file, file+'~')
        except OSError:
            # fail silently if we can't make a backup
            pass
    return open(file, 'w')

def write_skels(fileprefix, prefix, module):
    fp = open_with_backup(fileprefix+'module.c')
    fp.write(module_init_template % { 'prefix': prefix, 'module': module })
    fp.close()
    fp = open_with_backup(fileprefix+'.override')
    fp.write(override_template % { 'prefix': prefix, 'module': module })
    fp.close()

if __name__ == '__main__':
    opts, args = getopt.getopt(sys.argv[1:], 'f:p:m:h',
                               ['file-prefix=', 'prefix=', 'module=', 'help'])
    fileprefix = None
    prefix = None
    module = None
    for opt, arg in opts:
        if opt in ('-f', '--file-prefix'):
            fileprefix = arg
        elif opt in ('-p', '--prefix'):
            prefix = arg
        elif opt in ('-m', '--module'):
            module = arg
        elif opt in ('-h', '--help'):
            print 'usage: mkskel.py -f fileprefix -p prefix -m module'
            sys.exit(0)
    if not fileprefix or not prefix or not module:
        print 'usage: mkskel.py -f fileprefix -p prefix -m module'
        sys.exit(1)
    write_skels(fileprefix, prefix, module)
