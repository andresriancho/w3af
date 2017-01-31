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
from functools import partial

from ruamel.ordereddict import ordereddict as OrderedDict

from w3af.core.data.misc.encoding import smart_unicode
from w3af.core.data.dc.generic.data_container import DataContainer
from w3af.core.data.constants.encodings import UTF8
from w3af.core.data.parsers.utils.encode_decode import urlencode
from w3af.core.data.dc.utils.token import DataToken
from w3af.core.data.dc.utils.filter_printable import filter_non_printable


ERR_MSG_NO_REP = 'Unsupported init_val "%s", expected format is [("b", "2")]'


class NonRepeatKeyValueContainer(DataContainer, OrderedDict):
    """
    This class represents a data container for data which doesn't allow
    repeated parameter names.

    The DataContainer supports things like a=1&a=2 for query strings, but for
    example HTTP headers can't be repeated (by RFC) and thus we don't
    need any repeated parameter names.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, init_val=(), encoding=UTF8, relaxed_order=False):
        DataContainer.__init__(self, encoding=encoding)
        OrderedDict.__init__(self, relax=relaxed_order)

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
                    raise TypeError(ERR_MSG_NO_REP % init_val)

                if key in self:
                    raise TypeError(ERR_MSG_NO_REP % init_val)

                if not isinstance(val, (basestring, DataToken)):
                    raise TypeError(ERR_MSG_NO_REP % init_val)

                self[key] = val

    def __reduce__(self):
        """
        :return: Return state information for pickling
        """
        init_val = [[k, self[k]] for k in self]
        encoding = self.encoding

        token = self.token

        return self.__class__, (init_val, encoding), {'token': token}

    def __setstate__(self, state):
        self.token = state['token']

    def get_type(self):
        return 'Generic non-repeat key value container'

    def _to_str_with_separators(self, key_val_sep, pair_sep):
        """
        :return: Join all the values stored in this data container using the
                 specified separators.
        """
        lst = []

        # pylint: disable=E1133
        for k, v in self.items():
            to_app = u'%s%s%s' % (k, key_val_sep,
                                  smart_unicode(v, encoding=UTF8))
            lst.append(to_app)
        # pylint: enable=E1133

        return pair_sep.join(lst)

    def iter_setters(self):
        """
        :yield: Tuples containing:
                    * The name of this token as a string
                    * The token value
                    * The token path
                    * The setter to modify the value
        """
        # pylint: disable=E1133
        for k, v in self.items():
            if self.token_filter((k,), v):
                yield k, v, (k,), partial(self.__setitem__, k)
        # pylint: enable=E1133

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

    def get_short_printable_repr(self):
        """
        :return: A string with a short printable representation of self
        """
        if len(filter_non_printable(str(self))) <= self.MAX_PRINTABLE:
            return filter_non_printable(str(self))

        if self.get_token() is not None:
            # I want to show the token variable and value in the output
            # pylint: disable=E1133
            for k, v in self.items():
                if isinstance(v, DataToken):
                    dt_str = '%s=%s' % (filter_non_printable(v.get_name()),
                                        filter_non_printable(v.get_value()))
                    return '...%s...' % dt_str[:self.MAX_PRINTABLE]
            # pylint: enable=E1133
        else:
            # I'll simply show the first N parameter and values until the
            # MAX_PRINTABLE is achieved
            return filter_non_printable(str(self))[:self.MAX_PRINTABLE]
