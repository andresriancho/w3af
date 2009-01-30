# -*- Mode: Python; py-indent-offset: 4 -*-
# pygtk - Python bindings for the GTK toolkit.
# Copyright (C) 2006  Johan Dahlin
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

# Private to PyGTK, do not use in applications

import sys
from types import ModuleType

class LazyModule(object):
    def __init__(self, name, locals):
        self._name = name
        self._locals = locals
        self._modname = '%s.%s' % (self._locals.get('__name__'), self._name)

    def __getattr__(self, attr):
        module = __import__(self._name, self._locals, {}, ' ')
        sys.modules[self._modname] = module
        if attr == '__members__':
            return dir(module)
        return getattr(module, attr)

class _NotLoadedMarker:
    pass
_marker = _NotLoadedMarker()

class LazyDict(dict):
    def __init__(self, module):
        self._module = module
        dict.__init__(self)

    def __getitem__(self, name):
        print name
        return getattr(self._module, name)

class LazyNamespace(ModuleType):
    def __init__(self, module, locals):
        ModuleType.__init__(self, locals['__name__'])
        self._imports = {}

        ns = self.__dict__
        ns.update(locals)
        ns['__module__'] = self
        lazy_symbols = {}
        for symbol in module._get_symbol_names():
            lazy_symbols[symbol] = ns[symbol] = _marker

        ns.update(__dict__=LazyDict(self),
                  __bases__=(ModuleType,),
                  add_submodule=self.add_submodule)

        def __getattribute__(_, name):
            v = ns.get(name, _marker)
            if v is not _marker:
                return v
            if name in lazy_symbols:
                s = module._get_symbol(ns, name)
                return s
            elif name in self._imports:
                m = __import__(self._imports[name], {}, {}, ' ')
                ns[name] = m
                return m

            raise AttributeError(name)
        LazyNamespace.__getattribute__ = __getattribute__

    def add_submodule(self, name, importname):
        self._imports[name] = importname

