"""
html.py

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
import re

import w3af.core.data.parsers.parser_cache as parser_cache

from w3af.plugins.grep.password_profiling_plugins.base_plugin import BasePwdProfilingPlugin


WORD_SPLIT_RE = re.compile("[^\w]", re.UNICODE)


class html(BasePwdProfilingPlugin):
    """
    This plugin creates a map of possible passwords by reading html responses.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        BasePwdProfilingPlugin.__init__(self)

    def get_words(self, response):
        """
        Get words from the body, this is a modified "strings" that filters out
        HTML tags.

        :param response: In most common cases, an html. Could be almost anything
        :return: A map of strings:repetitions.
        """
        if not response.is_text_or_html():
            return {}

        data = {}
        split = WORD_SPLIT_RE.split

        def filter_by_len(x):
            return len(x) > 3

        for tag in parser_cache.dpc.get_tags_by_filter(response, None, yield_text=True):

            text = tag.text

            if text is None:
                continue

            # Words inside <title> weights more.
            inc = (tag.name == 'title') and 5 or 1

            # Filter by length of the word (> 3)
            for w in filter(filter_by_len, split(text)):
                if w in data:
                    data[w] += inc
                else:
                    data[w] = inc

        return data
