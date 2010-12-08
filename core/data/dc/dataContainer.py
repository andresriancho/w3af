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

from core.data.parsers.encode_decode import urlencode
import copy


class dataContainer(dict):
    '''
    This class represents a data container. It's basically the way query string
    and post-data is stored when using url-encoding.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, init_val=(), strict=False):
        self.strict = strict
        dict.__init__(self)
        
        if isinstance(init_val, dataContainer):
            self._sequence = init_val.keys()
            dict.update(self, init_val)
        elif isinstance(init_val, dict):
            # we lose compatibility with other ordered dict types this way
            raise TypeError('Undefined order, cannot get items from dict')
        else:
            self._sequence = []

            for item in init_val:
                try:
                    key, val = item
                except TypeError:
                    raise TypeError('key, val = item')
                self[key] = val
                
    def __str__( self ):
        '''
        This method returns a string representation of the dataContainer Object.
        
        @return: string representation of the dataContainer Object.
        '''
        return urlencode( self )
        #return urllib.urlencode( self )
        
    def copy(self):
        '''
        This method returns a copy of the dataContainer Object.
        
        @return: A copy of myself.
        '''
        return copy.deepcopy(self)
        
