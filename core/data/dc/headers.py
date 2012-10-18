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
from core.data.dc.dataContainer import DataContainer


class Headers(DataContainer):
    '''
    This class represents the set of HTTP request headers. 
    
    @author: Javier Andalia (jandalia AT gmail DOT com)
    '''
    def __init__(self, init_val=(), encoding=UTF8):
        super(Headers, self).__init__(init_val, encoding)
        
    def iget(self, header_name, default=None):
        '''
        @param header_name: The name of the header we want the value for
        @return: The value for a header given a name (be case insensitive)
        '''
        for stored_header_name in self:
            if header_name.lower() == stored_header_name.lower():
                return self[stored_header_name]
        return default

    def __setitem__(self, k, v):
        if isinstance(k, unicode):
            k = k.encode(self.encoding, 'replace').title()
        if isinstance(v, unicode):
            v = v.encode(self.encoding, 'replace')
        super(Headers, self).__setitem__(k, v)
    
    def __str__(self):
        '''
        >>> str(Headers({'HoST': u'w3af.com', 'AccEpt': '*/*'}.items()))
        'HoST: w3af.com\\nAccEpt: */*\\n'

        >>> repr(Headers({'Host': u'w3af.com', 'AccEpt': '*/*'}.items()))
        "Headers({'Host': 'w3af.com', 'AccEpt': '*/*'})"

        @return: string representation of the Headers() object.
        '''
        return self._to_str_with_separators(u': ', u'\n') + u'\n'
    
    def __unicode__(self):
        return str(self).decode(self.encoding)