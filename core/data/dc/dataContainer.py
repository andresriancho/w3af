# -*- coding: utf-8 -*-
'''
dataContainer.py

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
import copy

from core.data.constants.encodings import DEFAULT_ENCODING
import core.data.parsers.encode_decode as enc_dec


class dataContainer(dict):
    '''
    This class represents a data container. It's basically the way query string
    and post-data is stored when using url-encoding.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, init_val=(), encoding=DEFAULT_ENCODING):
        
        dict.__init__(self)
        
        self.encoding = encoding
        
        if isinstance(init_val, dataContainer):
            dict.update(self, init_val)
        elif isinstance(init_val, dict):
            # we lose compatibility with other ordered dict types this way
            raise TypeError('Undefined order, cannot get items from dict')
        else:
            for item in init_val:
                try:
                    key, val = item
                except TypeError:
                    raise TypeError('key, val = item')
                self[key] = val
                
    def __str__(self):
        '''
        This method returns a string representation of the dataContainer Object.
        
        >>> str(dataContainer([('a','1'), ('b', ['2','3'])]))
        'a=1&b=2&b=3'
        >>> import urllib
        >>> dc = dataContainer([('a','1'), ('u', u'Ú-ú-Ü-ü')], 'latin1')
        >>> urllib.unquote(str(dc)).decode('latin-1') == u'a=1&u=Ú-ú-Ü-ü'
        True

        @return: string representation of the dataContainer Object.
        '''
        return enc_dec.urlencode(self, encoding=self.encoding)
        
    def copy(self):
        '''
        This method returns a copy of the dataContainer Object.
        
        @return: A copy of myself.
        '''
        return copy.deepcopy(self)
       
