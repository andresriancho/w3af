"""
cookie.py

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
import re

from w3af.core.data.constants.encodings import DEFAULT_ENCODING
from w3af.core.data.dc.generic.kv_container import KeyValueContainer

KEY_VALUE_RE = re.compile('(.*?)=(.*?);')


class Cookie(KeyValueContainer):
    """
    This class represents a cookie.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, cookie_str='', encoding=DEFAULT_ENCODING):

        super(Cookie, self).__init__(encoding=encoding)

        for k, v in KEY_VALUE_RE.findall(cookie_str + ';'):
            k = k.strip()
            v = v.strip()

            # This was added to support repeated cookie names
            if k in self:
                self[k].append(v)
            else:
                self[k] = [v, ]

    def _sanitize(self, value):
        value = value.replace('\n', '%0a')
        value = value.replace('\r', '%0d')
        return value

    def get_type(self):
        return 'Cookie'

    def __str__(self):
        """
        This method returns a string representation of the cookie Object.

        :return: string representation of the cookie object.
        """
        cookie_pairs = []

        for token in self.iter_tokens():
            ks = self._sanitize(str(token.get_name()))
            vs = self._sanitize(str(token.get_value()))
            cookie_pairs.append('%s=%s' % (ks, vs))

        return '; '.join(cookie_pairs)

    def __reduce__(self):
        r = list(super(Cookie, self).__reduce__())
        r[1] = (str(self),)
        return tuple(r)

    @classmethod
    def from_http_response(cls, http_response):
        """
        Create a cookie object from an HTTP response.
        """
        cookies = []

        # Get data from RESPONSE
        response_headers = http_response.get_headers()

        for hname, hvalue in response_headers.iteritems():
            if 'cookie' in hname.lower():
                cookies.append(hvalue)

        cookie_inst = cls(''.join(cookies))

        #
        # delete everything that the browsers usually keep to themselves, since
        # this cookie object is the one we're going to send to the wire
        #
        for key in ['path', 'expires', 'domain', 'max-age']:
            try:
                del cookie_inst[key]
            except:
                pass

        return cookie_inst
