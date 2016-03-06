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
from w3af.core.data.context.utils import encode_payloads, decode_payloads


STRING_DELIMITERS = {'"', "'"}


class StyleContext(BaseContext):
    def can_break(self):
        """
        :return: All the strings in CAN_BREAK are required to break out of
                 the context and perform a successful XSS
        """
        return self.all_in(self.CAN_BREAK, self.payload)

    def get_payloads(self):
        if not self.CAN_BREAK:
            return {}

        return {''.join(self.CAN_BREAK)}


class GenericStyleContext(StyleContext):
    # These break characters are required for exploits like:
    # <div style="background-image: url(javascript:alert('XSS'))">
    CAN_BREAK = {':', '('}


class StyleStringGeneric(GenericStyleContext):
    ATTR_DELIMITER = None

    def can_break(self):
        """
        :return: True if we can break out
        """

        escaped = False
        for i, c in enumerate(self.payload):
            if c == '\\':
                escaped = not escaped
            elif c == self.ATTR_DELIMITER and not escaped:
                return self.all_in(self.CAN_BREAK, self.payload[i:])
            else:
                escaped = False

        return False

    def get_payloads(self):
        breaks = ''.join(self.CAN_BREAK)
        payload = '%s%s' % (self.ATTR_DELIMITER, breaks)
        return {payload, '\\%s' % payload}


class StyleSingleQuoteString(StyleStringGeneric):
    ATTR_DELIMITER = "'"


class StyleDoubleQuoteString(StyleStringGeneric):
    ATTR_DELIMITER = '"'


class StyleComment(StyleContext):
    CAN_BREAK = {'*/', ':', '('}


ALL_CONTEXTS = [GenericStyleContext, StyleSingleQuoteString,
                StyleDoubleQuoteString, StyleComment]


def get_css_context(data, boundary):
    """
    :param data: The CSS Style code where the payload might be in
    :param boundary: The payload border as sent to the web application

    :return: A list which contains lists of all contexts where the payload lives
    """
    return [c for c in get_css_context_iter(data, boundary)]


def get_css_context_iter(data, boundary):
    """
    We parse the CSS Style code and find the payload context name.

    :param data: The CSS Style code where the payload might be in
    :param boundary: The payload border as sent to the web application

    :return: A context iterator
    """
    for bound in boundary:
        if bound not in data:
            return

    # We replace the "context breaking payload" with an innocent string
    data = encode_payloads(boundary, data)

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
                    payloads, content = decode_payloads(context_content)
                    for payload in payloads:
                        if string_delim == "'":
                            yield StyleSingleQuoteString(payload,
                                                         content,
                                                         boundary)
                        else:
                            yield StyleDoubleQuoteString(payload,
                                                         content,
                                                         boundary)

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
                        payloads, content = decode_payloads(context_content)
                        for payload in payloads:
                            yield StyleComment(payload,
                                               content,
                                               boundary)
                    inside_comment = False
                    context_content = ''
            continue

        # Handle the string starts
        if c in STRING_DELIMITERS:

            # This analyzes the context content before the string start
            if CONTEXT_DETECTOR in context_content:
                payloads, content = decode_payloads(context_content)
                for payload in payloads:
                    yield GenericStyleContext(payload,
                                              content,
                                              boundary)

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
                    payloads, content = decode_payloads(context_content)
                    for payload in payloads:
                        yield GenericStyleContext(payload,
                                                  content,
                                                  boundary)

                context_content = ''
                continue

    # Handle the remaining bytes from the CSS code:
    if CONTEXT_DETECTOR in context_content:
        payloads, content = decode_payloads(context_content)
        for payload in payloads:
            yield GenericStyleContext(payload, content, boundary)
