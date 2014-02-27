"""
request_mixin.py

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

CR = '\r'
LF = '\n'
CRLF = CR + LF
SP = ' '

class RequestMixIn(object):
    def dump(self):
        """
        :return: a DETAILED str representation of this fuzzable request.
        """
        return u"%s%s%s" % (self.dump_request_head(),
                           CRLF, str(self.get_data() or ''))

    def get_request_line(self):
        """Return request line."""
        return u"%s %s HTTP/1.1%s" % (self.get_method(),
                                     self.get_uri().url_encode(),
                                     CRLF)

    def dump_request_head(self):
        """
        :return: A string with the head of the request
        """
        return u"%s%s" % (self.get_request_line(), self.dump_headers())

    def dump_headers(self):
        """
        :return: A string representation of the headers.
        """
        return unicode(self.get_headers())    