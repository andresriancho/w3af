'''
file_option.py

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

'''
import os

from core.controllers.exceptions import w3afException
from core.data.options.baseoption import BaseOption
from core.data.options.option_types import INPUT_FILE


class InputFileOption(BaseOption):

    _type = INPUT_FILE

    def set_value(self, value):
        '''
        @param value: The value parameter is set by the user interface, which
        for example sends 'True' or 'a,b,c'

        Based on the value parameter and the option type, I have to create a nice
        looking object like True or ['a','b','c'].
        '''
        if value == '':
            self._value = value
            return

        self._value = self.validate(value)

    def validate(self, value):

        directory = os.path.abspath(os.path.dirname(value))
        if not os.path.isdir(directory):
            msg = 'Invalid input file option value "%s", the directory does not'\
                  ' exist.'
            raise w3afException(msg % value)

        if not os.access(directory, os.R_OK):
            msg = 'Invalid input file option value "%s", the user doesn\'t have' \
                  ' enough permissions to read from the specified directory.'
            raise w3afException(msg % value)

        if not os.path.exists(value):
            msg = 'Invalid input file option value "%s", the specified file' \
                  ' does not exist.'
            raise w3afException(msg % value)

        if not os.access(value, os.R_OK):
            msg = 'Invalid input file option value "%s", the user doesn\'t have' \
                  ' enough permissions to read the specified file.'
            raise w3afException(msg % value)

        if not os.path.isfile(value):
            msg = 'Invalid input file option value "%s", the path doesn\'t' \
                  ' point to a file.'
            raise w3afException(msg % value)

        return value
