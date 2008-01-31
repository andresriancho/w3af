'''
cookie.py

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

import re
from core.data.dc.dataContainer import dataContainer
import copy

class cookie(dataContainer):
    '''
    This class represents a cookie.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, strValues='', strict=False):
        
        for k, v in re.findall('(.*?)=(.*?);', strValues + ';' ):
            self[ k.strip() ] = v.strip()
    
    def _sanitize( self, value ):
        value = value.replace('\n','%0a')
        value = value.replace('\r','%0d')
        return value
        
    def __str__( self ):
        '''
        This method returns a string representation of the cookie Object.
        
        @return: string representation of the cookie Object.
        '''
        res = ''
        for k in self:
            ks = self._sanitize( k )
            vs = self._sanitize( self[k] )
            res += ks + '=' + vs + '; '
        return res[:-1]
        
    def copy(self):
        '''
        This method returns a copy of the cookie Object.
        
        @return: A copy of myself.
        '''
        return copy.copy( self )
