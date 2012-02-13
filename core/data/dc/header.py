'''
header.py

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


class Header(DataContainer):
    '''
    This class represents a Request Header.
    
    @author: Javier Andalia (jandalia AT gmail DOT com)
    '''
    def __init__(self, init_val=None, encoding=UTF8):
        super(Header, self).__init__((), encoding)
        if init_val:
            self.update(init_val)

    def __setitem__(self, k, v):
        if isinstance(k, unicode):
            k = k.encode(self.encoding, 'replace').title()
        if isinstance(v, unicode):
            v = v.encode(self.encoding, 'replace')
        super(Header, self).__setitem__(k, v)
    
    def __str__(self):
        '''
        >>> str(Header({'HoST': u'w3af.com', 'AccEpt': ' */*'}))
        'Host: w3af.com\\nAccept:  */*\\n'
        >>> repr(Header({'Host': u'w3af.com', 'AccEpt': ' */*'}))
        "Header({'Host': 'w3af.com', 'AccEpt': ' */*'})"

        @return: string representation of the QueryString object.
        '''
        return ''.join("%s: %s%s" % (h.title(), v, '\n')
                       for h, v in self.iteritems())
    
    def __unicode__(self):
        return str(self).decode(self.encoding)