"""
esmre_multire.py

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

import esmre
import re

from w3af.core.data.constants.encodings import DEFAULT_ENCODING


class esmre_multire(object):
    """
    This is a wrapper around esmre that provides the plugins (users) with an
    easy to use API to esmre.
    """

    def __init__(self, re_list, re_compile_flags=0):
        """

        :param re_list: A list with all the regular expressions that we want
        to match against one or more strings using the "query" function.

        This list might be [re_str_1, re_str_2 ... , re_str_N] or something like
        [ (re_str_1, obj1) , (re_str_2, obj2) ... , (re_str_N, objN)]. In the first
        case, if a match is found this class will return [ (match_obj, re_str_N, pattern_obj), ]
        in the second case we'll return [ (match_obj, re_str_N, pattern_obj, objN), ]

        """
        self._index = esmre.Index()
        self._re_cache = {}

        for item in re_list:

            if isinstance(item, tuple):
                regex = item[0]
                regex = regex.encode(DEFAULT_ENCODING)
                self._re_cache[regex] = re.compile(regex, re_compile_flags)
                self._index.enter(regex, item)
            elif isinstance(item, basestring):
                item = item.encode(DEFAULT_ENCODING)
                self._re_cache[item] = re.compile(item, re_compile_flags)
                self._index.enter(item, (item,))
            else:
                raise ValueError(
                    'Can NOT build esmre_multire with provided values.')

    def query(self, target_str):
        """
        Apply the regular expressions to the target_str and return a list
        according to the class __init__ documentation.

        :param target_str: The target string where the regular expressions are
        going to be applied. First we apply the esmre algorithm and then we do
        some magic of our own.

        See test_multire.py for examples.
        """
        result = []

        if isinstance(target_str, unicode):
            target_str = target_str.encode(DEFAULT_ENCODING)

        query_result_list = self._index.query(target_str)

        for query_result in query_result_list:
            # query_result is a tuple with the regular expression that matched
            # as the first object and the associated objects following
            matched_regex = query_result[0]
            regex_comp = self._re_cache[matched_regex]
            matchobj = regex_comp.search(target_str)
            if matchobj:
                resitem = [matchobj, matched_regex, regex_comp]
                resitem.extend(query_result[1:])
                result.append(resitem)

        return result
