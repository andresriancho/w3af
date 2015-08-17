"""
normalize.py

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
from cStringIO import StringIO
from io import SEEK_CUR


def normalize_html(data):
    """
    Replace the < and > tags inside attribute delimiters with their encoded
    versions.

    Do nothing for content inside HTML comments.

    :param data: A string with an HTML
    :return: Another string, with a modified HTML
    """
    #
    #   These constants are here because of performance
    #   https://wiki.python.org/moin/PythonSpeed/PerformanceTips
    #
    AMP_LT = '&lt;'
    AMP_GT = '&gt;'
    TAG_START = '<'
    TAG_END = '>'
    COMMENT_END = '--'
    COMMENT_START = '!--'
    ATTR_DELIMITERS = {'"', '`', "'"}

    # Move unicode to str if required
    if isinstance(data, unicode):
        data = data.encode('utf8')

    # Fast search and replace when more than one char needs to be searched
    repls = ("\\'", ''), ('\\"', '')
    data = reduce(lambda a, kv: a.replace(*kv), repls, data)

    # We'll use lists instead of strings for creating the result
    new_data = []
    append = new_data.append
    quote_character = None
    inside_comment = False
    data = StringIO(data)
    should_read = True

    while should_read:

        s = data.read(1)

        if not s:
            should_read = False

        elif s in ATTR_DELIMITERS:
            if quote_character and s == quote_character:
                quote_character = None
            elif not quote_character:
                quote_character = s

        elif s == TAG_START:
            position = data.tell()
            excl_dash_dash = data.read(3)
            data.seek(position)

            if excl_dash_dash == COMMENT_START:
                # We're in the presence of <!--
                inside_comment = True
            elif quote_character and not inside_comment:
                append(AMP_LT)
                continue

        elif s == TAG_END:

            if inside_comment:
                # Is this the closing of an HTML comment? Read some bytes back
                # and find if we have a dash-dash
                data.seek(-2, SEEK_CUR)
                dash_dash = data.read(2)
                if dash_dash == COMMENT_END:
                    inside_comment = False

            elif quote_character:
                # Inside a quoted attr, and not inside a comment.
                append(AMP_GT)
                continue

        append(s)

    return ''.join(new_data)

