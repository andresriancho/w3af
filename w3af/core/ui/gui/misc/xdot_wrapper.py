"""
xdot_wrapper.py

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
import cairo

from xdot import DotWidget


class WrappedDotWidget(DotWidget):
    def do_expose_event(self, event):
        """
        In some strange cases we're getting:
            Error: invalid matrix (not invertible)

        This issue was not fixed up-stream, so we're applying this ugly patch
        that avoids users from getting a crash (but will most likely show an
        empty widget).

        I don't care much about this bug since it only appears once every 6
        months or so in my issue tracker.

        :see: https://github.com/andresriancho/w3af/issues/726
        :see: https://github.com/jrfonseca/xdot.py/issues/1
        """
        # pylint: disable=E1101
        try:
            return DotWidget.do_expose_event(self, event)
        except cairo.Error:
            pass
        # pylint: enable=E1101
