"""
took_line.py

Copyright 2019 Andres Riancho

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
import time


import w3af.core.controllers.output_manager as om


class TookLine(object):

    TOKEN = '{seconds}'

    def __init__(self, msg_fmt):
        """
        :param msg_fmt: A string containing the message to be sent to the debug
                        log. The message should contain the TOKEN, which will be
                        replaced by the time spent between the creation of the
                        instance and the call to send().
        """
        self._msg_fmt = msg_fmt
        self._start = time.time()

    def send(self):
        spent = time.time() - self._start
        spent = '%.2f' % spent

        msg = self._msg_fmt.replace(self.TOKEN, spent)

        om.out.debug(msg)
