'''
headers.py

Copyright 2012 Andres Riancho

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
'''
from core.data.constants.encodings import UTF8
from core.data.dc.data_container import DataContainer
from core.data.misc.encoding import smart_unicode


class Headers(DataContainer):
    '''
    This class represents the set of HTTP request headers.

    :author: Javier Andalia (jandalia AT gmail DOT com)
    '''
    def __init__(self, init_val=(), encoding=UTF8):
        cleaned_vals = self.clean_values(init_val)
        super(Headers, self).__init__(cleaned_vals, encoding)

    @classmethod
    def from_string(cls, headers_str):
        '''
        :param headers_str: A string with the HTTP headers, example:
            Server: Apache
            Content-Length: 123
        '''
        res = []
        splitted_str = headers_str.split('\r\n')
        for one_header_line in splitted_str:
            
            if not one_header_line:
                continue
            
            name, value = one_header_line.split(':', 1)
            
            # Escape the space after the ":"
            value = value[1:]
            
            res.append((name, value))
        
        return cls(res)
 
    
    def clean_values(self, init_val):        
        if isinstance(init_val, DataContainer)\
        or isinstance(init_val, dict):
            return init_val

        cleaned_vals = []

        # Cleanup whatever came from the wire into a unicode string
        for key, value in init_val:
            # I can do this key, value thing because the headers do NOT
            # have multiple header values like query strings and post-data
            if isinstance(value, basestring):
                value = smart_unicode(value)
            
            cleaned_vals.append( (smart_unicode(key), value) )
        
        return cleaned_vals
    
    def iget(self, header_name, default=None):
        '''
        :param header_name: The name of the header we want the value for
        :return: The value for a header given a name (be case insensitive)
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

    def __setitem__(self, k, v):
        if isinstance(k, basestring):
            k = k.encode(self.encoding, 'replace')
        else:
            raise ValueError('Header name must be a string.')

        if isinstance(v, basestring):
            v = v.encode(self.encoding, 'replace')
        #
        # Had to remove this for clone_with_list_values
        #else:
        #    raise ValueError('Header value must be a string.')

        super(Headers, self).__setitem__(k, v)

    def __str__(self):
        '''
        >>> str(Headers({'HoST': u'w3af.com', 'AccEpt': '*/*'}.items()))
        'HoST: w3af.com\\r\\nAccEpt: */*\\r\\n'

        >>> repr(Headers({'Host': u'w3af.com', 'AccEpt': '*/*'}.items()))
        "Headers({'Host': 'w3af.com', 'AccEpt': '*/*'})"

        :return: string representation of the Headers() object.
        '''
        return self._to_str_with_separators(u': ', u'\r\n') + u'\r\n'

    def __unicode__(self):
        return str(self).decode(self.encoding)
