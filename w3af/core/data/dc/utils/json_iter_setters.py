"""
json_iter_setters.py

Copyright 2014 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import json
import types

from w3af.core.data.dc.utils.token import DataToken


KEY_STRING = 'string'
KEY_OBJECT = 'object'
KEY_ARRAY = 'list'
KEY_NUMBER = 'number'
KEY_NULL = 'null'
KEY_BOOLEAN = 'boolean'

TO_WRAP_OBJS = (int, float, basestring, types.NoneType)


def json_iter_setters(arbitrary_python_obj):
    marbitrary_python_obj = to_mutable(arbitrary_python_obj)

    for k, v, s in _json_iter_setters(marbitrary_python_obj):
        yield k, v, s


def to_mutable(arbitrary_python_obj):
    """
    :param arbitrary_python_obj: Any arbitrary python object (which comes form
                                 json.loads). A combination of string, list,
                                 int, float, none and boolean.

    :return: We replace these [0] basic types with a wrapper object which allows
             me to provide a setter for those objects.

    [0] TO_WRAP_OBJS
    """
    if isinstance(arbitrary_python_obj, TO_WRAP_OBJS):
        return MutableWrapper(arbitrary_python_obj)

    elif isinstance(arbitrary_python_obj, MutableWrapper):
        value = to_mutable(arbitrary_python_obj.get_value())
        arbitrary_python_obj.set_value(value)
        return arbitrary_python_obj

    elif isinstance(arbitrary_python_obj, list):
        for idx, oapo in enumerate(arbitrary_python_obj):
            arbitrary_python_obj[idx] = to_mutable(oapo)

        return arbitrary_python_obj

    elif isinstance(arbitrary_python_obj, dict):
        for key, oapo in arbitrary_python_obj.iteritems():
            arbitrary_python_obj[key] = to_mutable(oapo)

        return arbitrary_python_obj


class MutableWrapper(object):
    """
    Wrapper around string, int and float which allows me to provide a setter
    around them. The
    """
    def __init__(self, wrapped_obj):
        self._wrapped_obj = wrapped_obj

    def get_value(self):
        return self._wrapped_obj

    def set_value(self, new_value):
        self._wrapped_obj = new_value

    def __getattr__(self, attr):
        # see if this object has attr
        # NOTE do not use hasattr, it goes into infinite recursion
        if attr in self.__dict__:
            # this object has it
            return getattr(self, attr)
        # proxy to the wrapped object
        return getattr(self._wrapped_obj, attr)


def _json_iter_setters(marbitrary_python_obj, key_names=[]):
    if isinstance(marbitrary_python_obj, MutableWrapper):
        # We get here when we're iterating over a MutableWrapper, which is a
        # helper class to be able to "change the value of a string|float|int"

        value = marbitrary_python_obj.get_value()

        if isinstance(value, basestring):
            key_names = key_names[:]
            key_names.append(KEY_STRING)
            yield '-'.join(key_names), value, marbitrary_python_obj.set_value

        elif isinstance(value, (int, float)):
            key_names = key_names[:]
            key_names.append(KEY_NUMBER)
            yield '-'.join(key_names), value, marbitrary_python_obj.set_value

        elif isinstance(value, bool):
            key_names = key_names[:]
            key_names.append(KEY_BOOLEAN)
            yield '-'.join(key_names), value, marbitrary_python_obj.set_value

        elif value is None:
            key_names = key_names[:]
            key_names.append(KEY_NULL)
            yield '-'.join(key_names), value, marbitrary_python_obj.set_value

        elif isinstance(value, DataToken):
            for k, v, s in _json_iter_setters(value, key_names=key_names):
                yield k, v, s
        else:
            for k, v, s in _json_iter_setters(value, key_names=key_names):
                yield k, v, s

    elif isinstance(marbitrary_python_obj, list):
        for idx, list_item in enumerate(marbitrary_python_obj):
            array_key_names = key_names[:]
            array_key_names.append(KEY_ARRAY)
            array_key_names.append(str(idx))

            for k, v, s in _json_iter_setters(list_item,
                                              key_names=array_key_names):
                yield k, v, s

    elif isinstance(marbitrary_python_obj, dict):
        for key, value in marbitrary_python_obj.iteritems():
            array_key_names = key_names[:]
            array_key_names.append(KEY_OBJECT)
            array_key_names.append(key)

            for k, v, s in _json_iter_setters(value, key_names=array_key_names):
                yield k, v, s


def json_complex_str(arbitrary_json):
    def encode_complex(obj):
        if isinstance(obj, DataToken):
            return obj.get_value()
        elif isinstance(obj, MutableWrapper):
            return obj.get_value()

        raise TypeError(repr(obj) + " is not JSON serializable")

    return json.dumps(arbitrary_json, default=encode_complex)