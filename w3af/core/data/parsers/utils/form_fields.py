"""
form_fields.py

Copyright 2015 Andres Riancho

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
from w3af.core.data.parsers.utils.form_constants import (INPUT_TYPE_SELECT,
                                                         INPUT_TYPE_RADIO,
                                                         INPUT_TYPE_CHECKBOX,
                                                         INPUT_TYPE_FILE)


class FormFieldMixin(object):
    __slots__ = ('input_type', 'name', 'value')

    def __init__(self, input_type, name, value):
        self.input_type = input_type
        self.name = name
        self.value = value

    def __repr__(self):
        fmt = '<%s form field (name: "%s", value: "%s")>'
        return fmt % (self.input_type.title(), self.name, self.value)

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        if isinstance(other, basestring):
            return self.value == other

        if not isinstance(other, FormFieldMixin):
            return False

        return (self.input_type == other.input_type and
                self.name == other.name and
                self.value == other.value)

    def __getstate__(self):
        state = {k: getattr(self, k) for k in self.__slots__}
        return state

    def __setstate__(self, state):
        for k, v in state.iteritems():
            setattr(self, k, v)


class GenericFormField(FormFieldMixin):
    """
    Represent a "common" input type such as text, password, etc.
    """
    __slots__ = ('input_type', 'name', 'value', 'autocomplete')

    def __init__(self, input_type, name, value, autocomplete=False):
        super(GenericFormField, self).__init__(input_type, name, value)
        self.autocomplete = autocomplete


class ChooseFormField(FormFieldMixin):
    """
    :param values: A list with all the values this input can take
    :param value: The currently selected/enabled value
    """
    __slots__ = ('input_type', 'name', 'values', 'value')

    def __init__(self, name, values):
        super(ChooseFormField, self).__init__(None, name, None)
        self.values = values

        if values:
            self.value = values[0]

    def set_value(self, value):
        self.value = value

    def __eq__(self, other):
        if isinstance(other, basestring):
            return self.value == other

        if not isinstance(other, ChooseFormField):
            return False

        return (self.input_type == other.input_type and
                self.name == other.name and
                self.value == other.value and
                self.values == other.values)


class SelectFormField(ChooseFormField):
    """
    Represent a <select> with all the option values

        <select>
          <option value="volvo">Volvo</option>
          <option value="saab">Saab</option>
          <option value="mercedes">Mercedes</option>
          <option value="audi">Audi</option>
        </select>

    The "values" attribute would hold "volvo", "saab", "mercedes", "audi".
    """
    __slots__ = ('input_type', 'name', 'values', 'value')

    def __init__(self, name, values):
        super(SelectFormField, self).__init__(name, values)
        self.input_type = INPUT_TYPE_SELECT


class RadioFormField(ChooseFormField):
    """
    Represent a type="radio" with all the values in the "values" list.

        <form action="">
        <input type="radio" name="sex" value="male">Male<br>
        <input type="radio" name="sex" value="female">Female
        </form>

    The "values" attribute would hold "male" and "female"
    """
    __slots__ = ('input_type', 'name', 'values', 'value')

    def __init__(self, name, values):
        super(RadioFormField, self).__init__(name, values)
        self.input_type = INPUT_TYPE_RADIO


class CheckboxFormField(ChooseFormField):
    """
    Represent a type="radio" with all the values in the "values" list.

        <form action="demo_form.asp" method="get">
          <input type="checkbox" name="vehicle" value="Bike"> I have a bike
          <input type="checkbox" name="vehicle" value="Car" checked> I have a car
          <input type="submit" value="Submit">
        </form>

    The "values" attribute would hold "male" and "female"
    """
    __slots__ = ('input_type', 'name', 'values', 'value')

    def __init__(self, name, values):
        super(CheckboxFormField, self).__init__(name, values)
        self.input_type = INPUT_TYPE_CHECKBOX


class FileFormField(FormFieldMixin):
    """
    Represent a "common" input type such as text, password, etc.
    """
    __slots__ = ('input_type', 'name', 'value', 'file_name')

    def __init__(self, name, value=None, file_name=None):
        super(FileFormField, self).__init__(None, name, value)
        self.input_type = INPUT_TYPE_FILE
        self.file_name = file_name


def get_value_by_key(attrs, *args):
    """
    Helper to get attribute values for N attribute names (return first match
    only)

    :param attrs: The attributes for input
    :param args: The attributes we want to query
    :return: The first value for the attribute specified in args
    """
    for search_attr_key in args:
        for attr_key, attr_value in attrs.iteritems():
            if attr_key.lower() == search_attr_key:
                return attr_value
    return None
