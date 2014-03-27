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
    ('<\?(?! *xml)(?!xpacket).*\?>', 'PHP'),
    ('<%.*?%>', 'ASP or JSP'),
    ('<jsp:.*?>', 'JSP'),
    ('<!--\s*%.*?%(--)?>', 'PHP'),
    ('<!--\s*\?.*?\?(--)?>', 'ASP or JSP'),
    ('<!--\s*jsp:.*?(--)?>', 'JSP'),
)

_multi_re = multi_re(SOURCE_CODE, re.IGNORECASE | re.DOTALL)


def is_source_file(file_content):
    """
    :param file_content: The content of the http response body to analyze
    :return: A tuple with:
                a re.match object if the file_content matches a source code file,
                a string with the source code programming language
    """
    for match, _, _, lang in _multi_re.query(file_content):
        return (match, lang)

    return (None, None)
