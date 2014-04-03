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
    major, minor, micro, releaselevel, serial = sys.version_info
    if major == 2:
        if minor not in (6, 7):
            msg = 'Error: Python 2.%s found but Python 2.6 or 2.7 required.'
            print(msg % minor)
    elif major > 2:
        msg = 'It seems that you are running Python 3k, please let us know if' \
              ' w3af works as expected at w3af-develop@lists.sourceforge.net !'
        print(msg)
        sys.exit(1)


def mem_test(when):
    from w3af.core.controllers.profiling.ps_mem import get_memory_usage, human
    sorted_cmds, shareds, _, _ = get_memory_usage(None, True, True, True)
    cmd = sorted_cmds[0]
    msg = "%8sB Private + %8sB Shared = %8sB" % (human(cmd[1] - shareds[cmd[0]]),
                                                 human(shareds[cmd[
                                                               0]]), human(cmd[1])
                                                 )
    print 'Total memory usage %s: %s' % (when, msg)


def running_in_virtualenv():
    if hasattr(sys, 'real_prefix'):
        return True

    return False