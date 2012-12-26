'''
headers.py

Copyright 2012 Andres Riancho

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
from core.data.constants.encodings import UTF8
from core.data.dc.data_container import DataContainer
from core.data.misc.encoding import smart_unicode


class Headers(DataContainer):
    '''
    This class represents the set of HTTP request headers.

    @author: Javier Andalia (jandalia AT gmail DOT com)
    '''
    def __init__(self, init_val=(), encoding=UTF8):
        
        if isinstance(init_val, (list, tuple)):
            wrapped_init = []
            for key, val in init_val:
                wrapped_init.append( (key, [val,]) )
            
            init_val = wrapped_init
            
        super(Headers, self).__init__(init_val, encoding)
    
    def iget(self, header_name, default=None):
        '''
        @param header_name: The name of the header we want the value for
        @return: The value for a header given a name (be case insensitive)
        '''
        for stored_header_name in self:
            if header_name.lower() == stored_header_name.lower():
                return self[stored_header_name], stored_header_name

        return default, None

    def clone_with_list_values(self):
        clone = Headers()
        for key, value in self.iteritems():
            clone[key] = [value, ]
        return clone

    def __getitem__(self, k):
        return super(Headers, self).__getitem__(k)

    def __str__(self):
        return self._to_str_with_separators(u': ', u'\n', encode=True) + u'\n'

    def __unicode__(self):
        return self._to_str_with_separators(u': ', u'\n') + u'\n'

