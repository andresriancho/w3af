# -*- Mode: Python; py-indent-offset: 4 -*-
# pygtk - Python bindings for the GTK toolkit.
# Copyright (C) 2004-2006  Johan Dahlin
#
#   gtk/deprecation.py: deprecation helpers for gtk
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

import os
import sys
import warnings

from gtk._gtk import DeprecationWarning

def _is_pydoc():
    if sys.argv:
        name = os.path.basename(sys.argv[0])
        if 'pydoc' in name:
            return True

    return False

class _Deprecated:
    def __init__(self, module, funcname, oldname, modulename=''):
        self.module = module
        self.funcname = funcname
        self.oldname = oldname
        if modulename:
            self.modulename = modulename
        else:
            self.modulename = 'gtk'

    def __repr__(self):
        return '<deprecated function %s>' % (self.oldname)

    def __call__(self, *args, **kwargs):
        if type(self.module) == str:
            module = __import__(self.module, {}, {}, ' ')
        else:
            module = self.module
        func = getattr(module, self.funcname)
        if not _is_pydoc():
            message = 'gtk.%s is deprecated, use %s.%s instead' % (
                self.oldname, self.modulename, func.__name__)
            # DeprecationWarning is imported from _gtk, so it's not the same
            # as the one found in exceptions.
            warnings.warn(message, DeprecationWarning, 2)
        try:
            return func(*args, **kwargs)
        except TypeError, e:
            raise TypeError(str(e).replace(func.__name__, self.oldname))

class _DeprecatedConstant:
    def __init__(self, value, name, suggestion):
        self._v = value
        self._name = name
        self._suggestion = suggestion

    def _deprecated(self, value):
        if not _is_pydoc():
            message = '%s is deprecated, use %s instead' % (self._name,
                                                            self._suggestion)
            warnings.warn(message, DeprecationWarning, 3)
        return value

    __nonzero__ = lambda self: self._deprecated(self._v == True)
    __int__     = lambda self: self._deprecated(int(self._v))
    __str__     = lambda self: self._deprecated(str(self._v))
    __repr__    = lambda self: self._deprecated(repr(self._v))
    __cmp__     = lambda self, other: self._deprecated(cmp(self._v, other))
