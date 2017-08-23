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
from functools import partial

from ruamel.ordereddict import ordereddict as OrderedDict

from w3af.core.data.misc.encoding import smart_unicode
from w3af.core.data.dc.generic.data_container import DataContainer
from w3af.core.data.constants.encodings import UTF8
from w3af.core.data.parsers.utils.encode_decode import urlencode
from w3af.core.data.dc.utils.token import DataToken
from w3af.core.data.dc.utils.filter_printable import filter_non_printable


ERR_MSG = 'Unsupported init_val "%s", expected format is [(u"b", [u"2", u"3"])]'


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
                    raise TypeError(ERR_MSG % init_val)

                if key in self:
                    raise TypeError(ERR_MSG % init_val)

                if not isinstance(val, (list, tuple)):
                    raise TypeError(ERR_MSG % init_val)

                for sub_val in val:
                    if not isinstance(sub_val, (basestring, DataToken)):
                        raise TypeError(ERR_MSG % init_val)

                self[key] = val

    def __reduce__(self):
        """
        :return: Return state information for pickling
        """
        init_val = self.items()
        encoding = self.encoding
        token = self.token

        return self.__class__, (init_val, encoding), {'token': token}

    def __setstate__(self, state):
        self.token = state['token']

    def get_type(self):
        return 'Generic key value container'

    def __str__(self):
        """
        Return string representation.

        :return: string representation of the KeyValueContainer instance.
        """
        return urlencode(self, encoding=self.encoding)

    def __unicode__(self):
        """
        Return unicode representation
        """
        return self._to_str_with_separators(u'=', u'&', errors='percent_encode')

    def iter_setters(self):
        """
        :yield: Tuples containing:
                    * The name of this token as a string
                    * The token value
                    * The token path
                    * The setter to modify the value
        """
        # pylint: disable=E1133
        for k, v in self.iteritems():
            for idx, ele in enumerate(v):

                token_path = (k, idx)

                if self.token_filter(token_path, ele):
                    yield k, ele, token_path, partial(v.__setitem__, idx)
        # pylint: enable=E1133

    def _to_str_with_separators(self, key_val_sep, pair_sep, errors='strict'):
        """
        :return: Join all the values stored in this data container using the
                 specified separators.
        """
        lst = []

        # pylint: disable=E1133
        for key, value_list in self.items():
            for value in value_list:
                value = smart_unicode(value, encoding=UTF8, errors=errors)
                to_app = u'%s%s%s' % (key, key_val_sep, value)
                lst.append(to_app)
        # pylint: enable=E1133

        return pair_sep.join(lst)

    def get_short_printable_repr(self):
        """
        :return: A string with a short printable representation of self
        """
        printable_self = filter_non_printable(str(self))

        if len(printable_self) <= self.MAX_PRINTABLE:
            return printable_self

        if self.get_token() is not None:
            # I want to show the token variable and value in the output
            # pylint: disable=E1133
            for k, v in self.items():
                for ele in v:
                    if isinstance(ele, DataToken):
                        dt_str = '%s=%s' % (filter_non_printable(ele.get_name()),
                                            filter_non_printable(ele.get_value()))
                        return '...%s...' % dt_str[:self.MAX_PRINTABLE]
            # pylint: enable=E1133
        else:
            # I'll simply show the first N parameter and values until the
            # MAX_PRINTABLE is achieved
            return printable_self[:self.MAX_PRINTABLE]
