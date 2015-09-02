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
from .main import get_context, get_context_iter


"""
html.py

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

from w3af.core.data.context.context.base import BaseContext


class ScriptText(BaseContext):

    CAN_BREAK = {}

    @staticmethod
    def match(js_code):
        return True

    @staticmethod
    def is_executable(js_code):
        return True


class ScriptSingleLineComment(BaseContext):

    CAN_BREAK = {'\n', '\r'}

    @staticmethod
    def match(js_code):
        return BaseContext.is_inside_context(js_code, '//', '\n')


class ScriptMultiLineComment(BaseContext):

    CAN_BREAK = {'*', '/'}

    @staticmethod
    def match(js_code):
        return BaseContext.is_inside_context(js_code, '/*', '*/')


class StringGeneric(BaseContext):

    @staticmethod
    def _match(js_code, attr_delimiter):
        if not BaseContext.is_inside_context(js_code,
                                             attr_delimiter,
                                             attr_delimiter):
            return False

        return True


class ScriptSingleQuoteString(StringGeneric):
    """
    Matches alert('PAYLOAD');
    """

    ATTR_DELIMITER = "'"
    CAN_BREAK = {ATTR_DELIMITER}

    @staticmethod
    def match(js_code):
        return StringGeneric._match(js_code,
                                    ScriptSingleQuoteString.ATTR_DELIMITER)


class ScriptDoubleQuoteString(StringGeneric):
    """
    Matches alert("PAYLOAD");
    """

    ATTR_DELIMITER = '"'
    CAN_BREAK = {ATTR_DELIMITER}

    @staticmethod
    def match(js_code):
        return StringGeneric._match(js_code,
                                    ScriptDoubleQuoteString.ATTR_DELIMITER)


# Note that the order is important! The most specific contexts should be first
JS_CONTEXTS = [ScriptSingleLineComment,
               ScriptSingleQuoteString,
               ScriptDoubleQuoteString,
               ScriptMultiLineComment,
               ScriptText]


def get_js_context(data, payload):
    """
    :return: A list which contains lists of all contexts where the payload lives
    """
    return get_context(data, payload, JS_CONTEXTS)


def get_js_context_iter(data, payload):
    """
    :return: A context iterator
    """
    for context in get_context_iter(data, payload, JS_CONTEXTS):
        yield context
