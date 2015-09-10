"""
css.py

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
from StringIO import StringIO

from w3af.core.data.context.context.base import BaseContext
from w3af.core.data.context.constants import CONTEXT_DETECTOR

STRING_DELIMITERS = {'"', "'"}


class StyleContext(BaseContext):
    def can_break(self):
        """
        :return: All the strings in CAN_BREAK are required to break out of
                 the context and perform a successful XSS
        """
        return self.all_in(self.CAN_BREAK, self.payload)


class GenericStyleContext(StyleContext):
    # These break characters are required for exploits like:
    # <div style="background-image: url(javascript:alert('XSS'))">
    CAN_BREAK = {':', '('}


class StyleSingleQuoteString(StyleContext):
    CAN_BREAK = {"'", ':', '('}


class StyleDoubleQuoteString(StyleContext):
    CAN_BREAK = {'"', ':', '('}


class StyleComment(StyleContext):
    CAN_BREAK = {'*/', ':', '('}


ALL_CONTEXTS = [GenericStyleContext, StyleSingleQuoteString,
                StyleDoubleQuoteString, StyleComment]


def get_css_context(data, payload):
    """
    :return: A list which contains lists of all contexts where the payload lives
    """
    return [c for c in get_css_context_iter(data, payload)]


def get_css_context_iter(data, payload):
    """
    We parse the CSS Style code and find the payload context name.

    :return: A context iterator
    """
    if payload not in data:
        return

    # We replace the "context breaking payload" with an innocent string
    data = data.replace(payload, CONTEXT_DETECTOR)
    untidy = lambda text: text.replace(CONTEXT_DETECTOR, payload)

    inside_string = False
    escape_next = False
    string_delim = None
    inside_comment = False
    context_content = ''

    data_io = StringIO(data)

    while True:
        c = data_io.read(1)
        context_content += c

        if not c:
            # No more chars to read
            break

        # Handle string contents
        if inside_string:

            # Handle \ escapes inside strings
            if c == '\\':
                escape_next = True
                continue

            if escape_next:
                escape_next = False
                continue

            # Handle string end
            if c == string_delim:

                if CONTEXT_DETECTOR in context_content:
                    if string_delim == "'":
                        yield StyleSingleQuoteString(payload,
                                                     untidy(context_content))
                    else:
                        yield StyleDoubleQuoteString(payload,
                                                     untidy(context_content))

                context_content = ''
                inside_string = False

            # Go to the next char inside the string
            continue

        # Handle the content of a /* comment */
        if inside_comment:
            if c == '*':
                c = data_io.read(1)
                context_content += c

                if c == '/':
                    if CONTEXT_DETECTOR in context_content:
                        yield StyleComment(payload, untidy(context_content))
                    inside_comment = False
                    context_content = ''
            continue

        # Handle the string starts
        if c in STRING_DELIMITERS:

            # This analyzes the context content before the string start
            if CONTEXT_DETECTOR in context_content:
                yield GenericStyleContext(payload, untidy(context_content))

            inside_string = True
            string_delim = c
            context_content = ''
            continue

        # Handle the comment starts
        if c == '/':
            c = data_io.read(1)
            context_content += c

            if c == '*':
                inside_comment = True

                # This analyzes the context content before the comment start
                if CONTEXT_DETECTOR in context_content:
                    yield GenericStyleContext(payload, untidy(context_content))

                context_content = ''
                continue

    # Handle the remaining bytes from the CSS code:
    if CONTEXT_DETECTOR in context_content:
        yield GenericStyleContext(payload, untidy(context_content))
