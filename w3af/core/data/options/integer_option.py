"""
integer_option.py

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
from w3af.core.data.options.option_types import INT


class IntegerOption(BaseOption):

    _type = INT

    def set_value(self, value):
        """
        :param value: The value parameter is set by the user interface, which
        for example sends 'True' or 'a,b,c'

        Based on the value parameter and the option type, I have to create a nice
        looking object like True or ['a','b','c'].
        """
        self._value = self.validate(value)

    def validate(self, value):
        try:
            integer_value = int(value)
        except:
            msg = 'Invalid integer option value "%s".' % value
            raise BaseFrameworkException(msg)

        # If there are any options, we need to validate them now
        _min = self.get_options().get('min')
        _max = self.get_options().get('max')

        if _min is not None:
            if integer_value < _min:
                msg = 'Expected a value greater than %s.' % _min
                raise BaseFrameworkException(msg)

        if _max is not None:
            if integer_value > _max:
                msg = 'Expected a value lower than %s.' % _max
                raise BaseFrameworkException(msg)

        return integer_value
