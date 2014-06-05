# -*- coding: utf-8 -*-
"""
nr_kv_container.py

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
from w3af.core.data.misc.encoding import smart_unicode

from w3af.core.data.dc.tokens import DataToken
from w3af.core.controllers.misc.ordereddict import OrderedDict
from w3af.core.data.dc.data_container import DataContainer
from w3af.core.data.constants.encodings import UTF8
from w3af.core.data.parsers.encode_decode import urlencode

ERR_MSG_NO_REP = 'Not supported init_val, expected format is [("b", "2")]'


class NonRepeatKeyValueContainer(DataContainer, OrderedDict):
    """
    This class represents a data container for data which doesn't allow
    repeated parameter names.

    The DataContainer supports things like a=1&a=2 for query strings, but for
    example HTTP headers can't be repeated (by RFC) and thus we don't
    need any repeated parameter names.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, init_val=(), encoding=UTF8):
        DataContainer.__init__(self, encoding=encoding)
        OrderedDict.__init__(self)

        if isinstance(init_val, NonRepeatKeyValueContainer):
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

                if not isinstance(val, (basestring, DataToken)):
                    raise TypeError(ERR_MSG_NO_REP)

                self[key] = val

    def _to_str_with_separators(self, key_val_sep, pair_sep):
        """
        :return: Join all the values stored in this data container using the
                 specified separators.
        """
        lst = []

        for k, v in self.items():
            to_app = u'%s%s%s' % (k, key_val_sep,
                                  smart_unicode(v, encoding=UTF8))
            lst.append(to_app)

        return pair_sep.join(lst)

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