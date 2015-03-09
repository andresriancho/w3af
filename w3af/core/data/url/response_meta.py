"""
response_meta.py

Copyright 2015 Andres Riancho

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

# Used to log responses in deque
SUCCESS = 'Success'


class ResponseMeta(object):
    """
    Stores response meta-data to be able to track errors and timeouts in the
    extended urllib library.
    """
    def __init__(self, successful, message, rtt=None):
        self.successful = successful
        self.message = message
        self.rtt = rtt

    def __str__(self):
        args = (self.successful, self.message, self.rtt)
        return '<ResponseMeta (successful: %s, message: %s, rtt: %s)' % args