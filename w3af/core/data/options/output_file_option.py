"""
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

"""
import os

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.options.baseoption import BaseOption
from w3af.core.data.options.option_types import OUTPUT_FILE
from w3af.core.data.fuzzer.utils import rand_alpha

DEV_NULL = '/dev/null'


class OutputFileOption(BaseOption):

    _type = OUTPUT_FILE

    def set_value(self, value):
        """
        :param value: The value parameter is set by the user interface, which
        for example sends 'True' or 'a,b,c'

        Based on the value parameter and the option type, I have to create a
        nice looking object like True or ['a','b','c'].
        """
        self._value = self.validate(value)

    def validate(self, value):
        
        expanded_path = os.path.expanduser(value)

        # In some scenarios we want to allow the end-user to choose an output
        # file that doesn't actually write to disk
        #
        # For example, in output.text_file the user might want to log to the
        # text log, but doesn't care about the HTTP requests and responses. In
        # that case the user specifies /dev/null as the output
        if expanded_path == '/dev/null':
            return value

        # This is useful for testing, the user specifies a script with $rnd$ in the
        # output file name, w3af will replace that string with 5 random chars.
        #
        # The user can then run the same script over and over without caring about
        # overwriting his output files.
        rnd = rand_alpha(5)
        value = expanded_path = expanded_path.replace('$rnd$', rnd)

        directory = os.path.abspath(os.path.dirname(expanded_path))

        if os.path.isdir(expanded_path):
            msg = 'Invalid output file "%s", it must not be a directory.'
            raise BaseFrameworkException(msg % value)

        if not os.path.isdir(directory):
            msg = ('Invalid file option "%s", the directory "%s" does'
                   ' not exist.')
            raise BaseFrameworkException(msg % (value, directory))

        if not os.access(directory, os.W_OK):
            msg = ('Invalid file option "%s", the user does not have'
                   ' enough permissions to write to the specified directory.')
            raise BaseFrameworkException(msg % value)

        if os.path.exists(value):
            if not os.access(value, os.W_OK):
                msg = ('Invalid file option "%s", the user does not have'
                       ' enough permissions to write to the file.')
                raise BaseFrameworkException(msg % value)

        # Please note the following:
        #     >>> os.path.abspath(os.path.dirname(''))
        #     '/home/foobar/workspace/threading2'
        #
        # This is why we need this check:
        if value == '':
            msg = 'Invalid file option, you have to specify a non-empty value.'
            raise BaseFrameworkException(msg)

        return value
