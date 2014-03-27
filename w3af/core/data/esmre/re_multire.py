"""
re_multire.py

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

import re

from w3af.core.data.constants.encodings import DEFAULT_ENCODING


class re_multire(object):
    """
    This is a wrapper around the re object that provides the plugins (users)
    with an easy to use API. This is a transition class that will be used by
    w3af users which don't have the esmre package installed.
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
        self._re_cache = {}
        self._assoc_obj = {}

        for item in re_list:

            if isinstance(item, tuple):
                regex = item[0]
                regex = regex.encode(DEFAULT_ENCODING)
                self._re_cache[regex] = re.compile(regex, re_compile_flags)
                self._assoc_obj[regex] = item[1:]
            elif isinstance(item, basestring):
                item = item.encode(DEFAULT_ENCODING)
                self._re_cache[item] = re.compile(item, re_compile_flags)
            else:
                raise ValueError(
                    'Can NOT build re_multire with provided values.')

    def query(self, target_str):
        """
        Apply the regular expressions to the target_str and return a list
        according to the class __init__ documentation.

        :param target_str: The target string where the regular expressions are
        going to be applied. First we apply the esmre algorithm and then we do
        some magic of our own.

        See test_re.py for usage examples.
        """
        result = []

        if isinstance(target_str, unicode):
            target_str = target_str.encode(DEFAULT_ENCODING)

        for regex_str, compiled_regex in self._re_cache.iteritems():

            matchobj = compiled_regex.search(target_str)
            if matchobj:
                resitem = [matchobj, regex_str, compiled_regex]

                if regex_str in self._assoc_obj:
                    resitem.extend(self._assoc_obj[regex_str])

                result.append(resitem)

        return result
