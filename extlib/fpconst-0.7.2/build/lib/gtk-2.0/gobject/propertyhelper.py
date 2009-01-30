# -*- Mode: Python; py-indent-offset: 4 -*-
# pygobject - Python bindings for the GObject library
# Copyright (C) 2007 Johan Dahlin
#
#   gobject/propertyhelper.py: GObject property wrapper/helper
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

import _gobject
from gobject.constants import \
     TYPE_NONE, TYPE_INTERFACE, TYPE_CHAR, TYPE_UCHAR, \
     TYPE_BOOLEAN, TYPE_INT, TYPE_UINT, TYPE_LONG, \
     TYPE_ULONG, TYPE_INT64, TYPE_UINT64, TYPE_ENUM, \
     TYPE_FLAGS, TYPE_FLOAT, TYPE_DOUBLE, TYPE_STRING, \
     TYPE_POINTER, TYPE_BOXED, TYPE_PARAM, TYPE_OBJECT, \
     TYPE_PYOBJECT
from gobject.constants import \
     G_MINFLOAT, G_MAXFLOAT, G_MINDOUBLE, G_MAXDOUBLE, \
     G_MININT, G_MAXINT, G_MAXUINT, G_MINLONG, G_MAXLONG, \
     G_MAXULONG


class property(object):
    """
    Creates a new property which in conjunction with GObject subclass will
    create a property proxy:

    >>> class MyObject(gobject.GObject):
    >>> ... prop = gobject.property(type=str)

    >>> obj = MyObject()
    >>> obj.prop = 'value'

    >>> obj.prop
    'value'

    The API is similar to the builtin property:

    class AnotherObject(gobject.GObject):
        @gobject.property
        def prop(self):
            return ...

    Which will create a read-only property called prop.
    """

    class __metaclass__(type):
        def __repr__(self):
            return "<class 'gobject.property'>"

    def __init__(self, getter=None, setter=None, type=None, default=None,
                 nick='', blurb='', flags=_gobject.PARAM_READWRITE,
                 minimum=None, maximum=None):
        """
        @param  getter: getter to get the value of the property
        @type   getter: callable
        @param  setter: setter to set the value of the property
        @type   setter: callable
        @param    type: type of property
        @type     type: type
        @param default: default value
        @param    nick: short description
        @type     bick: string
        @param   blurb: long description
        @type    blurb: string
        @param flags:    parameter flags, one of:
        - gobject.PARAM_READABLE
        - gobject.PARAM_READWRITE
        - gobject.PARAM_WRITABLE
        - gobject.PARAM_CONSTRUCT
        - gobject.PARAM_CONSTRUCT_ONLY
        - gobject.PARAM_LAX_VALIDATION
        @keyword minimum:  minimum allowed value (int, float, long only)
        @keyword maximum:  maximum allowed value (int, float, long only)
        """

        if getter and not setter:
            setter = self._readonly_setter
        elif setter and not getter:
            getter = self._writeonly_getter
        elif not setter and not getter:
            getter = self._default_getter
            setter = self._default_setter
        self.getter = getter
        self.setter = setter

        if type is None:
            type = object
        self.type = self._type_from_python(type)
        self.default = self._get_default(default)
        self._check_default()

        if not isinstance(nick, basestring):
            raise TypeError("nick must be a string")
        self.nick = nick

        if not isinstance(blurb, basestring):
            raise TypeError("blurb must be a string")
        self.blurb = blurb

        if flags < 0 or flags > 32:
            raise TypeError("invalid flag value: %r" % (flags,))
        self.flags = flags

        if minimum is not None:
            if minimum < self._get_minimum():
                raise TypeError(
                    "Minimum for type %s cannot be lower than %d" % (
                    self.type, self._get_minimum()))
        else:
            minimum = self._get_minimum()
        self.minimum = minimum
        if maximum is not None:
            if maximum > self._get_maximum():
                raise TypeError(
                    "Maximum for type %s cannot be higher than %d" % (
                    self.type, self._get_maximum()))
        else:
            maximum = self._get_maximum()
        self.maximum = maximum

        self.name = None

        self._values = {}
        self._exc = None

    def __repr__(self):
        return '<gobject property %s (%s)>' % (
            self.name or '(uninitialized)',
            _gobject.type_name(self.type))

    def __get__(self, instance, klass):
        if instance is None:
            return self

        self._exc = None
        value = instance.get_property(self.name)
        if self._exc:
            exc = self._exc
            self._exc = None
            raise exc

        return value

    def __set__(self, instance, value):
        if instance is None:
            raise TypeError

        self._exc = None
        instance.set_property(self.name, value)
        if self._exc:
            exc = self._exc
            self._exc = None
            raise exc

    def _type_from_python(self, type):
        if type == int:
            return TYPE_INT
        elif type == bool:
            return TYPE_BOOLEAN
        elif type == long:
            return TYPE_LONG
        elif type == float:
            return TYPE_DOUBLE
        elif type == str:
            return TYPE_STRING
        elif type == object:
            return TYPE_PYOBJECT
        elif type == _gobject.GObject:
            return TYPE_OBJECT
        elif type in [TYPE_NONE, TYPE_INTERFACE, TYPE_CHAR, TYPE_UCHAR,
                      TYPE_INT, TYPE_UINT, TYPE_BOOLEAN, TYPE_LONG,
                      TYPE_ULONG, TYPE_INT64, TYPE_UINT64, TYPE_ENUM,
                      TYPE_FLAGS, TYPE_FLOAT, TYPE_DOUBLE, TYPE_POINTER,
                      TYPE_BOXED, TYPE_PARAM, TYPE_OBJECT, TYPE_STRING,
                      TYPE_PYOBJECT]:
            return type
        else:
            raise TypeError("Unsupported type: %r" % (type,))

    def _get_default(self, default):
        ptype = self.type
        if default is not None:
            return default

        if ptype in [TYPE_INT, TYPE_UINT, TYPE_LONG, TYPE_ULONG,
                     TYPE_INT64, TYPE_UINT64]:
            return 0
        elif ptype == TYPE_STRING:
            return ''
        elif ptype == TYPE_FLOAT or ptype == TYPE_DOUBLE:
            return 0.0
        else:
            return None

    def _check_default(self):
        ptype = self.type
        default = self.default
        if (ptype == TYPE_BOOLEAN and (default not in (True, False))):
            raise TypeError(
                "default must be True or False, not %r" % (default,))
        elif ptype == TYPE_PYOBJECT:
            if default is not None:
                raise TypeError("object types does not have default values")

    def _get_minimum(self):
        ptype = self.type
        if ptype in [TYPE_UINT, TYPE_ULONG, TYPE_UINT64]:
            return 0
        elif ptype == TYPE_FLOAT:
            return G_MINFLOAT
        elif ptype == TYPE_DOUBLE:
            return G_MINDOUBLE
        elif ptype == TYPE_INT:
            return G_MININT
        elif ptype == TYPE_LONG:
            return G_MINLONG
        elif ptype == TYPE_INT64:
            return -2 ** 62 - 1

        return None

    def _get_maximum(self):
        ptype = self.type
        if ptype == TYPE_UINT:
            return G_MAXUINT
        elif ptype == TYPE_ULONG:
            return G_MAXULONG
        elif ptype == TYPE_INT64:
            return 2 ** 62 - 1
        elif ptype == TYPE_UINT64:
            return 2 ** 63 - 1
        elif ptype == TYPE_FLOAT:
            return G_MAXFLOAT
        elif ptype == TYPE_DOUBLE:
            return G_MAXDOUBLE
        elif ptype == TYPE_INT:
            return G_MAXINT
        elif ptype == TYPE_LONG:
            return G_MAXLONG

        return None

    #
    # Getter and Setter
    #

    def _default_setter(self, instance, value):
        self._values[instance] = value

    def _default_getter(self, instance):
        return self._values.get(instance, self.default)

    def _readonly_setter(self, instance, value):
        self._exc = TypeError("%s property of %s is read-only" % (
            self.name, type(instance).__name__))

    def _writeonly_getter(self, instance):
        self._exc = TypeError("%s property of %s is write-only" % (
            self.name, type(instance).__name__))

    #
    # Public API
    #

    def get_pspec_args(self):
        ptype = self.type
        if ptype in [TYPE_INT, TYPE_UINT, TYPE_LONG, TYPE_ULONG,
                     TYPE_INT64, TYPE_UINT64, TYPE_FLOAT, TYPE_DOUBLE]:
            args = self._get_minimum(), self._get_maximum(), self.default
        elif ptype == TYPE_STRING or ptype == TYPE_BOOLEAN:
            args = (self.default,)
        elif ptype == TYPE_PYOBJECT:
            args = ()
        elif ptype == TYPE_OBJECT:
            args = ()
        else:
            raise NotImplementedError(ptype)

        return (self.type, self.nick, self.blurb) + args + (self.flags,)
