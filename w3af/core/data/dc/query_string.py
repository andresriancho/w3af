"""
query_string.py

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
import w3af.core.data.parsers.encode_decode as enc_dec

from w3af.core.data.constants.encodings import DEFAULT_ENCODING
from w3af.core.data.dc.data_container import DataContainer


class QueryString(DataContainer):
    """
    This class represents a Query String.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, init_val=(), encoding=DEFAULT_ENCODING):
        super(QueryString, self).__init__(init_val, encoding)

    def __str__(self):
        """
        >>> str(QueryString([('a','>'), ('b', ['a==1 && z >= 2','3>2'])]))
        'a=%3E&b=a%3D%3D1%20%26%26%20z%20%3E%3D%202&b=3%3E2'
        >>> str(QueryString([('a', 'x=/etc/passwd')]))
        'a=x%3D%2Fetc%2Fpasswd'

        :return: string representation of the QueryString object.
        """
        return enc_dec.urlencode(self, encoding=self.encoding, safe='')
