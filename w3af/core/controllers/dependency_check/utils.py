"""
utils.py

Copyright 2006 Andres Riancho

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
import sys


def verify_python_version():
    """
    Check python version eq 2.6 or 2.7
    """
    major, minor, micro, release_level, serial = sys.version_info
    if major == 2:
        if minor != 7:
            msg = 'Error: Python 2.%s found but Python 2.7 required.'
            print(msg % minor)
    elif major > 2:
        msg = ('It seems that you are running w3af using Python3, which is not'
               ' officially supported by the w3af team.\nTo force w3af to be'
               ' run using python2.7 run it as follows (depending on your OS):'
               '\n\n'
               ' * python2.7 w3af_console\n'
               ' * python2 w3af_console\n'
               '\n'
               'To make this change permanent modify the shebang line in the'
               ' w3af_console, w3af_gui and w3af_api scripts.')
        print(msg)
        sys.exit(1)


def running_in_virtualenv():
    if hasattr(sys, 'real_prefix'):
        return True

    return False