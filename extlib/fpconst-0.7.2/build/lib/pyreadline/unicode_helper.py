# -*- coding: utf-8 -*-
#*****************************************************************************
#       Copyright (C) 2007  Jorgen Stenarson. <jorgen.stenarson@bostream.nu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************
import sys

try:
    pyreadline_codepage=sys.stdout.encoding
except AttributeError:        #This error occurs when pdb imports readline and doctest has replaced 
                              #stdout with stdout collector
    pyreadline_codepage="ascii"   #assume ascii codepage
    

def ensure_unicode(text):
    """helper to ensure that text passed to WriteConsoleW is unicode"""
    if isinstance(text, str):
        return text.decode(pyreadline_codepage, "replace")
    return text

def ensure_str(text):
    """Convert unicode to str using pyreadline_codepage"""
    if isinstance(text, unicode):
        return text.encode(pyreadline_codepage, "replace")
    return text
