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

from collections import Iterable

import core.data.parsers.encode_decode as enc_dec

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

    def __str__(self):
        '''
        Return string representation.

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
        return self._to_str_with_separators(u'=', u'&')

    def _to_str_with_separators(self, key_val_sep, pair_sep):
        lst = []
        for k, v in self.items():
            if isinstance(v, basestring):
                v = [v]
            else:
                if not isinstance(v, Iterable):
                    v = [(v if v is None else unicode(v, UTF8))]

            for ele in v:
                if not ele:
                    toapp = k + key_val_sep
                else:
                    toapp = k + key_val_sep + ele
                lst.append(toapp)
        return pair_sep.join(lst)
