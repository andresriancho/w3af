'''
queryString.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''

from core.data.constants.encodings import DEFAULT_ENCODING
from core.data.dc.dataContainer import dataContainer
import core.data.parsers.encode_decode as enc_dec


class queryString(dataContainer):
    '''
    This class represents a Query String.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, init_val=(), strict=False, encoding=DEFAULT_ENCODING):
        dataContainer.__init__(self, init_val, encoding)

    def __str__(self):
        '''
        >>> str(queryString([('a','>'), ('b', ['a==1 && z >= 2','3>2'])]))
        'a=%3E&b=a%3D%3D1%20%26%26%20z%20%3E%3D%202&b=3%3E2'
        >>> str(queryString([('a', 'x=/etc/passwd')]))
        'a=x%3D%2Fetc%2Fpasswd'
    
        @return: string representation of the dataContainer Object.
        '''
        return enc_dec.urlencode(self, encoding=self.encoding, safe='')
    