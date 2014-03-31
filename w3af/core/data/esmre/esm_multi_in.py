# -*- encoding: utf-8 -*-
"""
esm_multi_in.py

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

"""

import esm

from w3af.core.data.constants.encodings import DEFAULT_ENCODING


class esm_multi_in(object):
    """
    This is a wrapper around esm that provides the plugins (users) with an
    easy to use API to esm for doing various "in" statements with better
    algorithms.
    """

    def __init__(self, in_list):
        """

        :param in_list: A list with all the strings that we want
        to match against one or more strings using the "query" function.

        This list might be [str_1, str_2 ... , str_N] or something like
        [ (str_1, obj1) , (str_2, obj2) ... , (str_N, objN)]. In the first
        case, if a match is found this class will return [ str_N, ]
        in the second case we'll return [ [str_N, objN], ]

        """
        self._index = esm.Index()

        for item in in_list:

            if isinstance(item, tuple):
                in_str = item[0]
                in_str = in_str.encode(DEFAULT_ENCODING)
                self._index.enter(in_str, item)
            elif isinstance(item, basestring):
                item = item.encode(DEFAULT_ENCODING)
                self._index.enter(item, (item,))
            else:
                raise ValueError(
                    'Can NOT build esm_multi_in with provided values.')

        self._index.fix()

    def query(self, target_str):
        """
        Run through all the "in" statements on top of target_str and return a list
        according to the class __init__ documentation.

        :param target_str: The target string where the in statements are
        going to be applied.

        """
        result = []
        if isinstance(target_str, unicode):
            target_str = target_str.encode(DEFAULT_ENCODING)

        query_result_list = self._index.query(target_str)

        for query_result in query_result_list:
            if len(query_result[1]) == 1:
                result.append(list(query_result[1:][0])[0])
            else:
                result.append(list(query_result[1:][0]))

        return result
