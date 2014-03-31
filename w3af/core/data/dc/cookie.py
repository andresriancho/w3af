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
from w3af.core.data.dc.data_container import DataContainer


class Cookie(DataContainer):
    """
    This class represents a cookie.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, cookie_str='', encoding=DEFAULT_ENCODING):

        super(Cookie, self).__init__(encoding=encoding)

        for k, v in re.findall('(.*?)=(.*?);', cookie_str + ';'):
            k = k.strip()
            v = v.strip()

            # This was added to support repeated parameter names
            if k in self:
                self[k].append(v)
            else:
                self[k] = [v, ]

    def _sanitize(self, value):
        value = value.replace('\n', '%0a')
        value = value.replace('\r', '%0d')
        return value

    def __str__(self):
        """
        This method returns a string representation of the cookie Object.

        :return: string representation of the cookie object.
        """
        res = ''
        for parameter_name in self:
            for element_index in xrange(len(self[parameter_name])):
                ks = self._sanitize(parameter_name)
                vs = self._sanitize(self[parameter_name][element_index])
                res += ks + '=' + vs + '; '
        return res[:-1]

    def __reduce__(self):
        r = list(super(Cookie, self).__reduce__())
        r[1] = (str(self),)
        return tuple(r)
