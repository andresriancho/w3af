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
import hashlib

CR = '\r'
LF = '\n'
CRLF = CR + LF
SP = ' '


class RequestMixIn(object):

    __slots__ = ()

    def dump(self, ignore_headers=()):
        """
        :return: The HTTP request as it would be sent to the wire, with a minor
                 change, instead of using the path in the second token of the
                 request we use the URL, this is just a user-friendly feature

                 Please note that we're returning a byte-string, with the
                 special characters in the headers and URL encoded as expected
                 by the RFC, and the POST-data (potentially) holding raw bytes
                 such as an image content.
        """
        data = self.get_data() or ''

        request_head = self.dump_request_head(ignore_headers=ignore_headers)
        request_head = request_head.encode('utf-8')

        return '%s%s%s' % (request_head, CRLF, data)

    def get_request_hash(self, ignore_headers=()):
        """
        :return: Hash the request (as it would be sent to the wire) and return
        """
        return hashlib.md5(self.dump(ignore_headers=ignore_headers)).hexdigest()

    def get_request_line(self):
        """
        :return: request first line as sent to the wire.
        """
        return u'%s %s HTTP/1.1%s' % (self.get_method(),
                                      self.get_uri().url_encode(),
                                      CRLF)

    def dump_request_head(self, ignore_headers=()):
        """
        :return: A string with the head of the request
        """
        return u'%s%s' % (self.get_request_line(),
                          self.dump_headers(ignore_headers=ignore_headers))

    def dump_headers(self, ignore_headers=()):
        """
        :return: A string representation of the headers.
        """
        try:
            # For FuzzableRequest
            headers = self.get_all_headers()
        except AttributeError:
            # For HTTPRequest
            headers = self.get_headers()

        # Ignore the headers specified in the kwarg parameter
        for header_name in ignore_headers:
            try:
                headers.idel(header_name)
            except KeyError:
                # That's fine, if it doesn't exist we just continue
                continue

        return unicode(headers)
