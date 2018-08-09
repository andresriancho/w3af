"""
multi_re.py

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
import re
import esmre

from acora import AcoraBuilder
from w3af.core.data.constants.encodings import DEFAULT_ENCODING


class MultiRE(object):

    def __init__(self, regexes_or_assoc, re_compile_flags=0, hint_len=3):
        """
        :param re_compile_flags: The regular expression compilation flags

        :param hint_len: Use only hints larger than hint_len to speed-up the search.

        :param regexes_or_assoc: A list with all the regular expressions that
                                 we want to match against one or more strings
                                 using the "query" function.

                                This list might look like:
                                    [re_str_1, re_str_2 ... , re_str_N]

                                Or something like:
                                    [(re_str_1, obj1), ..., (re_str_N, objN)].

                                In the first case, if a match is found this class
                                will return:
                                    [(match_obj, re_str_N, compiled_regex),]

                                In the second case we'll return:
                                    [(match_obj, re_str_N, compiled_regex, objN),]
        """
        self._regexes_or_assoc = regexes_or_assoc
        self._re_compile_flags = re_compile_flags
        self._hint_len = hint_len
        self._translator = dict()
        self._re_cache = dict()
        self._keyword_to_re = dict()
        self._regexes_with_no_keywords = list()
        self._acora = self._build()

    def _build(self):
        builder = AcoraBuilder()

        for idx, item in enumerate(self._regexes_or_assoc):

            #
            #   First we compile all regular expressions and save them to
            #   the re_cache.
            #
            if isinstance(item, tuple):
                regex = item[0]
                regex = regex.encode(DEFAULT_ENCODING)
                self._re_cache[regex] = re.compile(regex, self._re_compile_flags)

                if regex in self._translator:
                    raise ValueError('Duplicated regex "%s"' % regex)

                self._translator[regex] = item[1:]
            elif isinstance(item, basestring):
                regex = item.encode(DEFAULT_ENCODING)
                self._re_cache[regex] = re.compile(regex, self._re_compile_flags)
            else:
                raise ValueError('Can NOT build MultiRE with provided values.')

            #
            #   Now we extract the string literals (longer than hint_len only) from
            #   the regular expressions and populate the acora index
            #
            regex_hints = esmre.hints(regex)
            regex_keywords = esmre.shortlist(regex_hints)

            if not regex_keywords:
                self._regexes_with_no_keywords.append(regex)
                continue

            # Get the longest one
            regex_keyword = regex_keywords[0]

            if len(regex_keyword) <= self._hint_len:
                self._regexes_with_no_keywords.append(regex)
                continue

            # Add this keyword to the acora index, and also save a way to associate the
            # keyword with the regular expression
            regex_keyword = regex_keyword.lower()
            builder.add(regex_keyword)

            regexes_matching_keyword = self._keyword_to_re.get(regex_keyword, [])
            regexes_matching_keyword.append(regex)
            self._keyword_to_re[regex_keyword] = regexes_matching_keyword

        return builder.build()

    def query(self, target_str):
        """
        Run through all the regular expressions and identify them in target_str.

        We'll only run the regular expressions if:
             * They do not have keywords
             * The keywords exist in the string

        :param target_str: The target string where the keywords need to be match
        :yield: (match_obj, re_str_N, compiled_regex)
        """
        if isinstance(target_str, unicode):
            target_str = target_str.encode(DEFAULT_ENCODING)

        #
        #   Match the regular expressions that have keywords and those
        #   keywords are found in the target string by acora
        #
        seen = set()
        target_str = target_str.lower()

        for match, position in self._acora.finditer(target_str):
            if match in seen:
                continue

            seen.add(match)

            for regex in self._keyword_to_re[match]:
                compiled_regex = self._re_cache[regex]

                matchobj = compiled_regex.search(target_str)
                if matchobj:
                    yield self._create_output(matchobj, regex, compiled_regex)

        #
        #   Match the regular expressions that don't have any keywords
        #
        for regex_without_keyword in self._regexes_with_no_keywords:
            compiled_regex = self._re_cache[regex_without_keyword]

            matchobj = compiled_regex.search(target_str)
            if matchobj:
                yield self._create_output(matchobj, regex_without_keyword, compiled_regex)

    def _create_output(self, matchobj, regex, compiled_regex):
        extra_data = self._translator.get(regex, None)

        if extra_data is None:
            return matchobj, regex, compiled_regex
        else:
            all_data = [matchobj, regex, compiled_regex]
            all_data.extend(extra_data)
            return all_data
