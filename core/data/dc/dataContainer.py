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

from core.data.constants.encodings import UTF8
from core.controllers.misc.ordereddict import OrderedDict
import core.data.parsers.encode_decode as enc_dec


class DataContainer(OrderedDict):
    '''
    This class represents a data container. It's basically the way
    query-string and post-data are stored when using url-encoding.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, init_val=(), encoding=UTF8):
        
        super(DataContainer, self).__init__()
        self.encoding = encoding
        
        if isinstance(init_val, DataContainer):
            self.update(init_val)
        elif isinstance(init_val, dict):
            # we lose compatibility with other ordered dict types this way
            raise TypeError('Undefined order, cannot get items from dict')
        else:
            for item in init_val:
                try:
                    key, val = item
                except TypeError:
                    raise TypeError('key, val = item')
                #BUGBUG: Do we have a bug here related to repeated parameters?
                self[key] = val
    
    def copy(self):
        '''
        This method returns a copy of the DataContainer Object.
        
        @return: A copy of myself.
        '''
        return copy.deepcopy(self)
       
    def __str__(self):
        '''
        Return string representation.
        
        >>> str(DataContainer([(u'a','1'), (u'b', ['2','3'])]))
        'a=1&b=2&b=3'
        >>> str(DataContainer([(u'aaa', None)]))
        'aaa='
        >>> str(DataContainer([(u'aaa', '')]))
        'aaa='
        >>> str(DataContainer([(u'aaa', (None, ''))]))
        'aaa=&aaa='
        >>> import urllib
        >>> dc = DataContainer([(u'a','1'), (u'u', u'Ú-ú-Ü-ü')], 'latin1')
        >>> urllib.unquote(str(dc)).decode('latin-1') == u'a=1&u=Ú-ú-Ü-ü'
        True

        @return: string representation of the DataContainer Object.
        '''
        return enc_dec.urlencode(self, encoding=self.encoding)
    
    def __unicode__(self):
        '''
        Return unicode representation
        
        >>> unicode(DataContainer([(u'a', u'1'), (u'b', [u'2', u'3'])]))
        u'a=1&b=2&b=3'
        >>> unicode(DataContainer([(u'aaa', None)]))
        u'aaa='
        >>> unicode(DataContainer([(u'aaa', u'')]))
        u'aaa='
        '''
        lst = []
        for k, v in self.items():
            if isinstance(v, basestring):
                v = [v]
            else:
                try:
                    # is this a sufficient test for sequence-ness?
                    len(v)
                except TypeError:
                    v = [(v if v is None else unicode(v, UTF8))]
            for ele in v:
                if not ele:
                    toapp = k + u'='
                else:
                    toapp = k + u'=' + ele
                lst.append(toapp)
        return u'&'.join(lst)
    
    