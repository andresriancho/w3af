"""
javascript.py

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
from StringIO import StringIO

from w3af.core.data.context.context.base import BaseContext
from w3af.core.data.context.constants import CONTEXT_DETECTOR

STRING_DELIMITERS = {'"', "'"}


class ScriptSingleLineComment(BaseContext):
    CAN_BREAK = {'\n', '\r'}


class ScriptMultiLineComment(BaseContext):
    CAN_BREAK = {'*/'}


class ScriptStringGeneric(BaseContext):
    pass


class ScriptSingleQuoteString(ScriptStringGeneric):
    """
    Matches alert('PAYLOAD');
    """
    ATTR_DELIMITER = "'"
    CAN_BREAK = {ATTR_DELIMITER}


class ScriptDoubleQuoteString(ScriptStringGeneric):
    """
    Matches alert("PAYLOAD");
    """
    ATTR_DELIMITER = '"'
    CAN_BREAK = {ATTR_DELIMITER}


class ScriptExecutableContext(BaseContext):
    """
    Matches things like:
        * alert(""); PAYLOAD()
        * PAYLOAD;
        * {"x": PAYLOAD}
    """
    CAN_BREAK = {}

    def is_executable(self):
        return True

ALL_CONTEXTS = [ScriptExecutableContext, ScriptDoubleQuoteString,
                ScriptSingleQuoteString, ScriptMultiLineComment,
                ScriptSingleLineComment]


def get_js_context(data, payload):
    """
    :return: A list which contains lists of all contexts where the payload lives
    """
    return [c for c in get_js_context_iter(data, payload)]


def get_js_context_iter(data, payload):
    """
    We parse the JavaScript code and find the payload context name.

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
    inside_single_line_comment = False
    inside_multi_line_comment = False
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
                        yield ScriptSingleQuoteString(payload,
                                                      untidy(context_content))
                    else:
                        yield ScriptDoubleQuoteString(payload,
                                                      untidy(context_content))

                context_content = ''
                inside_string = False

            # Go to the next char inside the string
            continue

        # Handle the content of a // Comment
        if inside_single_line_comment:

            # Handle the end of a comment
            if c in {'\n', '\r'}:
                if CONTEXT_DETECTOR in context_content:
                    yield ScriptSingleLineComment(payload,
                                                  untidy(context_content))
                inside_single_line_comment = False
                context_content = ''
            continue

        # Handle the content of a /* multi line comment */
        if inside_multi_line_comment:
            if c == '*':
                c = data_io.read(1)
                context_content += c

                if c == '/':
                    if CONTEXT_DETECTOR in context_content:
                        yield ScriptMultiLineComment(payload,
                                                     untidy(context_content))
                    inside_multi_line_comment = False
                    context_content = ''
            continue

        # Handle the string starts
        if c in STRING_DELIMITERS:

            # This analyzes the context content before the string start
            if CONTEXT_DETECTOR in context_content:
                yield ScriptExecutableContext(payload,
                                              untidy(context_content))

            inside_string = True
            string_delim = c
            context_content = ''
            continue

        # Handle the comment starts
        if c == '/':
            c = data_io.read(1)
            context_content += c

            if c == '/':
                inside_single_line_comment = True

            if c == '*':
                inside_multi_line_comment = True

            if inside_multi_line_comment or inside_single_line_comment:
                # This analyzes the context content before the comment start
                if CONTEXT_DETECTOR in context_content:
                    yield ScriptExecutableContext(payload,
                                                  untidy(context_content))

                context_content = ''
                continue

    # Handle the remaining bytes from the JS code:
    if CONTEXT_DETECTOR in context_content:
        yield ScriptExecutableContext(payload,
                                      untidy(context_content))
