"""
is_source_file.py

Copyright 2010 Andres Riancho

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
from w3af.core.data.esmre.multi_re import multi_re

SOURCE_CODE = (
    ('<\?php .*?\?>', 'PHP'),
    ('<\?php\n.*?\?>', 'PHP'),       # These two are required for perf #2129
    ('<\?php\r.*?\?>', 'PHP'),       # and are repeated over the list

    # Need to review how to re-add these in the future
    # https://github.com/andresriancho/w3af/issues/2129
    #
    #('<\? .*?\?>', 'PHP'),
    #('<\?\n.*?\?>', 'PHP'),
    #('<\?\r.*?\?>', 'PHP'),

    ('<% .*?%>', 'ASP or JSP'),
    ('<%\n.*?%>', 'ASP or JSP'),
    ('<%\r.*?%>', 'ASP or JSP'),

    ('<%@ .*?%>', 'ASPX'),          # http://goo.gl/zEjHA4
    ('<%@\n.*?%>', 'ASPX'),
    ('<%@\r.*?%>', 'ASPX'),

    ('<asp:.*?%>', 'ASPX'),
    ('<jsp:.*?>', 'JSP'),

    ('<%! .*%>', 'JSP'),
    ('<%!\n.*%>', 'JSP'),
    ('<%!\r.*%>', 'JSP'),
    ('<%=.*%>', 'JSP or PHP'),

    ('<!--\s*%.*?%(--)?>', 'PHP'),
    ('<!--\s*\?.*?\?(--)?>', 'ASP or JSP'),
    ('<!--\s*jsp:.*?(--)?>', 'JSP'),
)

BLACKLIST = {'xml', 'xpacket'}

_multi_re = multi_re(SOURCE_CODE, re.IGNORECASE | re.DOTALL, hint_len=2)


def is_source_file(file_content):
    """
    :param file_content: The content of the http response body to analyze
    :return: A tuple with:
                - re.match object if the file_content matches a source code file
                - string with the source code programming language
    """
    for match, _, _, lang in _multi_re.query(file_content):

        match_str = match.group(0)

        for blacklist_str in BLACKLIST:
            if blacklist_str in match_str:
                break
        else:
            return match, lang

    return None, None
