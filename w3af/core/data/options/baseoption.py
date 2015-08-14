"""
baseoption.py

Copyright 2008 Andres Riancho

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
import copy
import cgi


class BaseOption(object):
    """
    This class represents an option.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, name, default_value, desc, _help='', tabid=''):
        """
        :param name: The name of the option
        :param default_value: The default value of the option
        :param desc: The description of the option
        :param type: boolean, integer, string, etc..
        :param _help: The help of the option; a large description of the option
        :param tabid: The tab id of the option
        """
        # To be set by set_value and to avoid pylint error
        self._value = None
        self.set_value(default_value)
        self._default_value = self._value

        self._name = name
        self._desc = desc
        self._help = _help
        self._tabid = tabid

    def get_name(self):
        return self._name

    def get_desc(self):
        return self._desc

    def get_default_value(self):
        """
        :return: The object, as it was set using set_default_value / set_value
                 or the __init__
        """
        return self._default_value

    def get_value(self):
        return self._value

    # And the string versions of the above methods...
    def _get_str(self, value):
        return str(value)

    def get_default_value_str(self):
        return self._get_str(self.get_default_value())

    def get_value_str(self):
        return self._get_str(self.get_value())

    def get_value_for_profile(self, self_contained=False):
        """
        Allows the option to be serialized differently when used as a profile
        value.

        Added when fixing:
            https://github.com/andresriancho/w3af/issues/402

        :param self_contained: If set to True the profile option will be
                               serialized in such a way that it can be read in
                               full from the profile. For example, if the option
                               is a file, the contents are read and stored as
                               the value.
        """
        return self._get_str(self.get_value())

    def get_type(self):
        return self._type

    def get_help(self):
        return self._help

    def get_tabid(self):
        return self._tabid

    def set_name(self, v):
        self._name = v

    def set_desc(self, v):
        self._desc = v

    def set_default_value(self, v):
        self._default_value = v

    def set_value(self, value):
        """
        :param value: The value parameter is set by the user interface, which
        for example sends 'True' or 'a,b,c'

        Based on the value parameter and the option type, I have to create a nice
        looking object like True or ['a','b','c']. This replaces the *old*
        parseOptions.
        """
        raise NotImplementedError

    def validate(self, value):
        """
        Convenient method for GUI to call for each change in the input text to
        show a yellow background when the value is invalid. This was part of a
        refactoring to reduce duplicated code for each option type where the
        validation code was in ipport_option.py and in entries.py and in some
        cases they differ.

        Each option type should implement this.

        :return: The validated value (which in the GUI can be ignored) or a
                 BaseFrameworkException when the value is invalid.
        """
        raise NotImplementedError

    def set_type(self, v):
        self._type = v

    def set_help(self, v):
        self._help = v

    def set_tabid(self, v):
        self._tabid = v

    def _sanitize(self, value):
        """
        Encode some values that can't be used in XML
        """
        # FIXME: Not 100% sure about this...
        # I should also kill the \a and other strange escapes...
        # Maybe there is already a function that does this!
        value = cgi.escape(value)
        value = value.replace('"', '&quot;')
        return value

    def __repr__(self):
        """
        A nice way of printing your object =)
        """
        fmt = '<option name:%s|type:%s|value:%s>'
        return fmt % (self._name, self._type, self._value)

    def __eq__(self, other):
        if not isinstance(other, BaseOption):
            return False

        name = self._name == other._name
        _type = self._type == other._type
        value = self._value == other._value
        return name and _type and value

    def copy(self):
        """
        This method returns a copy of the option Object.

        :return: A copy of myself.
        """
        return copy.deepcopy(self)
