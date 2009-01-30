# -*- Mode: Python; py-indent-offset: 4 -*-
# pygobject - Python bindings for the GObject library
# Copyright (C) 2006  Johan Dahlin
#
#   gobject/__init__.py: initialisation file for gobject module
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

# this can go when things are a little further along
try:
    import ltihooks
    ltihooks # pyflakes
    del ltihooks
except ImportError:
    pass

from gobject.constants import *
from _gobject import *
_PyGObject_API = _gobject._PyGObject_API

from propertyhelper import property

class GObjectMeta(type):
    "Metaclass for automatically registering GObject classes"
    def __init__(cls, name, bases, dict_):
        type.__init__(cls, name, bases, dict_)
        cls._install_properties()
        cls._type_register(cls.__dict__)

    def _install_properties(cls):
        gproperties = getattr(cls, '__gproperties__', {})

        props = []
        for name, prop in cls.__dict__.items():
            if isinstance(prop, property): # not same as the built-in
                if name in gproperties:
                    raise ValueError
                prop.name = name
                gproperties[name] = prop.get_pspec_args()
                props.append(prop)

        if not props:
            return

        cls.__gproperties__ = gproperties

        if (hasattr(cls, 'do_get_property') or
            hasattr(cls, 'do_set_property')):
            for prop in props:
                if (prop.getter != prop._default_getter or
                    prop.setter != prop._default_setter):
                    raise TypeError(
                        "GObject subclass %r defines do_get/set_property"
                        " and it also uses a property which a custom setter"
                        " or getter. This is not allowed" % (cls,))

        def obj_get_property(self, pspec):
            name = pspec.name.replace('-', '_')
            prop = getattr(cls, name, None)
            if prop:
                return prop.getter(self)
        cls.do_get_property = obj_get_property

        def obj_set_property(self, pspec, value):
            name = pspec.name.replace('-', '_')
            prop = getattr(cls, name, None)
            if prop:
                prop.setter(self, value)
        cls.do_set_property = obj_set_property

    def _type_register(cls, namespace):
        ## don't register the class if already registered
        if '__gtype__' in namespace:
            return

        if not ('__gproperties__' in namespace or
                '__gsignals__' in namespace or
                '__gtype_name__' in namespace):
            return

        type_register(cls, namespace.get('__gtype_name__'))

_gobject._install_metaclass(GObjectMeta)

del _gobject
