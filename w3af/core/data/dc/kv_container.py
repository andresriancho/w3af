# -*- coding: utf-8 -*-
"""
kv_container.py

Copyright 2014 Andres Riancho

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

"""
import copy

from w3af.core.data.misc.encoding import smart_unicode

from w3af.core.data.dc.tokens import DataToken
from w3af.core.controllers.misc.ordereddict import OrderedDict
from w3af.core.data.dc.data_container import DataContainer
from w3af.core.data.constants.encodings import UTF8
from w3af.core.data.parsers.encode_decode import urlencode


ERR_MSG = 'Not supported init_val, expected format is [(u"b", [u"2", u"3"])]'


class KeyValueContainer(DataContainer, OrderedDict):
    """
    This class represents a data container. It's basically the way
    query-string and post-data are stored when using url-encoding.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, init_val=(), encoding=UTF8):
        DataContainer.__init__(self, encoding=encoding)
        OrderedDict.__init__(self)

        if isinstance(init_val, KeyValueContainer):
            self.update(init_val)
        elif isinstance(init_val, dict):
            # we lose compatibility with other ordered dict types this way
            raise TypeError('Undefined order, cannot get items from dict')
        else:
            for item in init_val:
                try:
                    key, val = item
                except TypeError:
                    raise TypeError(ERR_MSG)

                if key in self:
                    raise TypeError(ERR_MSG)

                if not isinstance(val, (list, tuple)):
                    raise TypeError(ERR_MSG)

                for sub_val in val:
                    if not isinstance(sub_val, (basestring, DataToken)):
                        raise TypeError(ERR_MSG)

                self[key] = val

        self.enforce_no_set = True

    def __str__(self):
        """
        Return string representation.

        :return: string representation of the DataContainer Object.
        """
        return urlencode(self, encoding=self.encoding)

    def __unicode__(self):
        """
        Return unicode representation
        """
        return self._to_str_with_separators(u'=', u'&')

    def iter_tokens(self):
        """
        DataToken instances unbound to any data container are (almost always)
        useless. Most likely you should use iter_bound_tokens

        :yield: DataToken instances to help in the fuzzing process of this
                DataContainer.
        """
        for k, v in self.items():
            for ele in v:
                yield DataToken(k, ele)

    def iter_bound_tokens(self):
        for k, v in self.items():
            for idx, ele in enumerate(v):
                token = DataToken(k, ele)

                dcc = copy.deepcopy(self)
                dcc[k][idx] = token
                dcc.set_token(token)

                yield dcc, token

    def _to_str_with_separators(self, key_val_sep, pair_sep):
        """
        :return: Join all the values stored in this data container using the
                 specified separators.
        """
        lst = []

        for k, v in self.items():
            for ele in v:
                to_app = u'%s%s%s' % (k, key_val_sep,
                                      smart_unicode(ele, encoding=UTF8))
                lst.append(to_app)

        return pair_sep.join(lst)
