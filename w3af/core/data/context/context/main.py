"""
main.py

Copyright 2015 Andres Riancho

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
from .html import (HtmlAttrSingleQuote, HtmlAttrDoubleQuote,
                   HtmlAttrBackticks, HtmlAttr, HtmlTag, HtmlText,
                   HtmlComment, HtmlTagClose)

# Note that the order is important!
CONTEXTS = [HtmlComment,
            HtmlAttrSingleQuote,
            HtmlAttrDoubleQuote,
            HtmlAttrBackticks,
            HtmlAttr,
            HtmlTag,
            HtmlTagClose,
            HtmlText]


def get_context(data, payload):
    """
    :return: A list which contains lists of all contexts where the payload lives
    """
    return [c for c in get_context_iter(data, payload)]


def get_context_iter(data, payload):
    """
    :return: A context iterator
    """
    chunks = data.split(payload)
    data = ''

    for chunk in chunks[:-1]:
        data += chunk

        for context_klass in CONTEXTS:
            if context_klass.match(data):
                context = context_klass()
                yield context
                break
