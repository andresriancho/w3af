# -*- coding: utf-8 -*-
"""
data_container.py

Copyright 2006 Andres Riancho

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

from collections import Iterable

import w3af.core.data.parsers.encode_decode as enc_dec

from w3af.core.data.db.disk_item import DiskItem
from w3af.core.data.constants.encodings import UTF8
from w3af.core.controllers.misc.ordereddict import OrderedDict


ERR_MSG = 'Not supported init_val, expected format is [(u"b", [u"2", u"3"])]'
ERR_MSG_NO_REP = 'Not supported init_val, expected format is [("b", "2")]'


class DataContainerMixin(OrderedDict, DiskItem):
    def copy(self):
        """
        This method returns a copy of the DataContainer Object.

        :return: A copy of myself.
        """
        return copy.deepcopy(self)

    def __str__(self):
        """
        Return string representation.

        :return: string representation of the DataContainer Object.
        """
        return enc_dec.urlencode(self, encoding=self.encoding)

    def __unicode__(self):
        """
        Return unicode representation
        """
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
                    to_app = k + key_val_sep
                else:
                    to_app = k + key_val_sep + ele
                lst.append(to_app)

        return pair_sep.join(lst)

    @property
    def _all_items(self):
        return ''.join(str((k, v)) for k, v in self.iteritems())

    def get_eq_attrs(self):
        return ['_all_items']


class DataContainer(DataContainerMixin):
    """
    This class represents a data container. It's basically the way
    query-string and post-data are stored when using url-encoding.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
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
                    raise TypeError(ERR_MSG)

                if key in self:
                    raise TypeError(ERR_MSG)

                if not isinstance(val, (list, tuple)):
                    raise TypeError(ERR_MSG)

                for sub_val in val:
                    if not isinstance(sub_val, basestring):
                        raise TypeError(ERR_MSG)

                self[key] = val


class NonRepeatDataContainer(DataContainerMixin):
    """
    This class represents a data container for data which doesn't allow
    repeated parameter names.

    The DataContainer supports things like a=1&a=2 for query strings, but for
    example HTTP headers can't be repeated (by RFC) and thus we don't
    need any repeated parameter names.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, init_val=(), encoding=UTF8):
        super(NonRepeatDataContainer, self).__init__()

        self.encoding = encoding

        if isinstance(init_val, NonRepeatDataContainer):
            self.update(init_val)
        elif isinstance(init_val, dict):
            # we lose compatibility with other ordered dict types this way
            raise TypeError('Undefined order, cannot get items from dict')
        else:
            for item in init_val:
                try:
                    key, val = item
                except TypeError:
                    raise TypeError(ERR_MSG_NO_REP)

                if key in self:
                    raise TypeError(ERR_MSG_NO_REP)

                if not isinstance(val, basestring):
                    raise TypeError(ERR_MSG_NO_REP)

                self[key] = val
