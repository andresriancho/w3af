"""
in_multi_in.py

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

from w3af.core.data.constants.encodings import DEFAULT_ENCODING


class in_multi_in(object):
    """
    This is a class that provides the plugins (users) with an easy to use API to
    perform various "in" statements on top of the same target string.
    """

    def __init__(self, str_list):
        """

        :param str_list: A list with all the strings that we want
        to match against one or more strings using the "query" function.

        This list might be [str_1, str_2 ... , str_N] or something like
        [ (str_1, obj1) , (str_2, obj2) ... , (str_N, objN)]. In the first
        case, if a match is found this class will return [ str_N, ]
        in the second case we'll return [ [str_N, objN], ]

        """
        self._in = []
        self._assoc_obj = {}

        for item in str_list:

            if isinstance(item, tuple):
                in_str = item[0]
                in_str = in_str.encode(DEFAULT_ENCODING)
                self._in.append(in_str)
                self._assoc_obj[in_str] = item[1:]
            elif isinstance(item, basestring):
                item = item.encode(DEFAULT_ENCODING)
                self._in.append(item)
            else:
                raise ValueError(
                    'Can NOT build in_multi_in with provided values.')

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

        for in_str in self._in:

            if in_str in target_str:

                if in_str in self._assoc_obj:
                    resitem = [in_str, ]
                    resitem.extend(self._assoc_obj[in_str])
                    result.append(resitem)
                else:
                    result.append(in_str)

        return result
