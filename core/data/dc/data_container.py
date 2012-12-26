# -*- coding: utf-8 -*-
'''
data_container.py

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
import urllib

from core.data.misc.encoding import smart_unicode
from core.data.constants.encodings import UTF8
from core.controllers.misc.ordereddict import OrderedDict


class DataContainer(OrderedDict):
    '''
    This class represents a data container. It's basically the way
    query-string and post-data are stored when using url-encoding.

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    def __init__(self, init_val=(), encoding=UTF8):
        super(DataContainer, self).__init__()
        self.encoding = encoding

        if isinstance(init_val, dict):
            # we lose compatibility with other ordered dict types this way
            raise TypeError('Undefined order, cannot get items from dict')

        if isinstance(init_val, DataContainer):
            self.update(init_val)
            return
                
        for item in init_val:
            try:
                key, val = item
            except TypeError:
                raise TypeError('DataContainer requires (key, val) in init')

            if key in self:
                msg = 'Not supported init_val, the way of using repeated' \
                      ' parameter names is [(u"b", [u"2", u"3"])]'
                raise TypeError(msg)
            
            if not isinstance(val, (list, tuple)):
                msg = 'Invalid type for dc ctor %s expected tuple or list.'
                raise TypeError(msg % type(val))

            if not all(isinstance(i, basestring) for i in val):
                msg = 'Invalid type for dc ctor expected tuple or list'\
                      ' containing strings.'
                raise TypeError(msg)
            
            self[key] = val

    def copy(self):
        '''
        This method returns a copy of the DataContainer Object.

        @return: A copy of myself.
        '''
        return copy.deepcopy(self)

    def __setitem__(self, k, v):
        if not isinstance(k, basestring):
            raise TypeError('DataContainer key must be a string.')

        if not isinstance(v, (list, tuple)):
            raise TypeError('DataContainer value must be list or tuple.')
        
        k = smart_unicode(k, encoding=self.encoding)
        v = [smart_unicode(i, encoding=self.encoding) for i in v]
        
        super(DataContainer, self).__setitem__(k, v)
        
    def __str__(self):
        '''
        Return string representation.

        @return: string representation of the DataContainer Object.
        '''
        return self._to_str_with_separators(u'=', u'&', encode=True)

    def __unicode__(self):
        '''
        Return unicode representation

        >>> unicode(DataContainer([(u'a', u'1'), (u'b', [u'2', u'3'])]))
        u'a=1&b=2&b=3'
        '''
        return self._to_str_with_separators(u'=', u'&')

    def _to_str_with_separators(self, key_val_sep, pair_sep, encode=False):
        '''
        @return: A string representation of self using key_val_sep as the
                 key/value separator and pair_sep as the separator between
                 different key/value pairs.
        '''
        lst = []
        
        for k, v_lst in self.items():
            for v in v_lst:
                
                if encode:
                    k = k.encode(self.encoding)
                    v = v.encode(self.encoding)
                    
                    k = urllib.quote(k, safe='/<>"\'=:()')
                    v = urllib.quote(v, safe='/<>"\'=:()')
                    
                to_append = k + key_val_sep + v
                lst.append(to_append)
                
        return pair_sep.join(lst)
