"""
multi_in.py

Copyright 2017 Andres Riancho

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
from acora import AcoraBuilder
from w3af.core.data.constants.encodings import DEFAULT_ENCODING


class MultiIn(object):
    def __init__(self, keywords_or_assoc):
        """
        :param keywords_or_assoc: A list with all the strings that we want
        to match against one or more strings using the "query" function.

        This list might be:
            [str_1, str_2 ... , str_N]

        Or something like:
            [(str_1, obj1) , (str_2, obj2) ... , (str_N, objN)].

        In the first case, if a match is found this class will return:
            [str_N,]

        In the second case we'll return
            [[str_N, objN],]
        """
        self._keywords_or_assoc = keywords_or_assoc
        self._translator = dict()
        self._acora = self._build()

    def _build(self):
        builder = AcoraBuilder()

        for idx, item in enumerate(self._keywords_or_assoc):

            if isinstance(item, tuple):
                keyword = item[0]
                keyword = keyword.encode(DEFAULT_ENCODING)

                if keyword in self._translator:
                    raise ValueError('Duplicated keyword "%s"' % keyword)

                self._translator[keyword] = item[1:]

                builder.add(keyword)
            elif isinstance(item, basestring):
                keyword = item.encode(DEFAULT_ENCODING)
                builder.add(keyword)
            else:
                raise ValueError('Can NOT build MultiIn with provided values.')

        return builder.build()

    def query(self, target_str):
        """
        Run through all the keywords and identify them in target_str

        :param target_str: The target string where the keywords need to be match
        :yield: The matches (see __init__)
        """
        if isinstance(target_str, unicode):
            target_str = target_str.encode(DEFAULT_ENCODING)

        seen = set()

        for match, position in self._acora.finditer(target_str):
            if match in seen:
                continue

            seen.add(match)
            extra_data = self._translator.get(match, None)

            if extra_data is None:
                yield match
            else:
                all_data = [match]
                all_data.extend(extra_data)
                yield all_data
