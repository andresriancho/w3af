"""
exec_decorator.py

Copyright 2010 Andres Riancho

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
from functools import wraps

import w3af.core.controllers.output_manager as om


def exec_debug(fn):

    @wraps(fn)
    def new(self, command):
        #   Run the original function
        result = fn(self, command)
        result = result if result is not None else ''
        no_newline_result = result.replace('\n', '')
        no_newline_result = no_newline_result.replace('\r', '')

        #   Format the message
        if len(no_newline_result) > 25:
            exec_result = '"%s..."' % no_newline_result[:25]
        else:
            exec_result = '"%s"' % no_newline_result[:25]

        msg = 'exec("%s", %s) == %s bytes' % (command, exec_result,
                                              len(exec_result))

        #   Print the message to the debug output
        om.out.debug(msg)

        #   Return the result
        return result

    return new
