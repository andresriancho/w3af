"""
bool_option.py

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
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.options.baseoption import BaseOption
from w3af.core.data.options.option_types import BOOL


class BoolOption(BaseOption):

    _type = BOOL

    def set_value(self, value):
        """
        :param value: The value parameter is set by the user interface, which
        for example sends 'True' or 'a,b,c'

        Based on the value parameter and the option type, I have to create a
        nice looking object like True or ['a','b','c'].
        """
        if isinstance(value, bool):
            self._value = value
            return

        self._value = self.validate(value)

    def validate(self, value):
        if value.lower() == 'true':
            validated_value = True
        elif value.lower() == 'false':
            validated_value = False
        else:
            msg = 'Invalid boolean option value "%s".' % value
            raise BaseFrameworkException(msg)

        return validated_value
