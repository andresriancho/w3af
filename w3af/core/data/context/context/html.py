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
import re

from w3af.core.data.context.context.javascript import get_js_context_iter
from w3af.core.data.context.context.base import BaseContext
from w3af.core.data.context.constants import JS_EVENTS, EXECUTABLE_ATTRS


class HtmlTag(BaseContext):
    """
    Matches <PAYLOAD></foo>
    """
    CAN_BREAK = {' ', '>'}


class HtmlTagClose(BaseContext):
    """
    Matches <foo></PAYLOAD>
    """
    CAN_BREAK = {' ', '>'}


class HtmlText(BaseContext):
    """
    Matches <tag attr="value">PAYLOAD</tag>
    """
    CAN_BREAK = {'<'}


class HtmlComment(BaseContext):
    """
    Matches <!-- PAYLOAD -->
    """
    CAN_BREAK = {'-', '>', '<'}


class HtmlAttr(BaseContext):
    """
    Matches <tag PAYLOAD="value" />
    """
    CAN_BREAK = {' ', '='}


class ScriptText(HtmlText):
    """
    Matches <script>PAYLOAD</script>
    """
    def can_break(self):
        # If we can break out of the context then we're done
        if super(ScriptText, self).can_break():
            return True

        script_text = self.get_context_content()

        for js_context in get_js_context_iter(script_text, self.payload):
            # At least one of the contexts where the payload is echoed in the
            # script text needs to be escaped from
            if js_context.can_break():
                return True

        return False

    def is_executable(self):
        script_text = self.get_context_content()

        for js_context in get_js_context_iter(script_text, self.payload):
            # At least one of the contexts where the payload is echoed in the
            # script text needs to be executable
            if js_context.is_executable():
                return True

        return False


class CSSText(HtmlText):
    """
    Matches <style>PAYLOAD</style>
    """
    def can_break(self):
        # If we can break out of the context then we're done
        if super(CSSText, self).can_break():
            return True

        raise NotImplementedError('Parse the CSS text!')

    def is_executable(self):
        raise NotImplementedError('Parse the CSS text!')


class HtmlDeclaration(BaseContext):
    """
    This method is called to handle an HTML doctype declaration
    (e.g. <!DOCTYPE html>).
    """
    CAN_BREAK = {'>'}


class HtmlProcessingInstruction(BaseContext):
    """
    For example, for the processing instruction <?proc color='red'>
    """
    CAN_BREAK = {'>'}


class HTMLAttrQuoteGeneric(BaseContext):

    JS_ATTRS = EXECUTABLE_ATTRS.union(JS_EVENTS)

    JS_PATTERN = re.compile('javascript:', re.IGNORECASE)
    VB_PATTERN = re.compile('vbscript:', re.IGNORECASE)

    def __init__(self, payload, attr_name, attr_value):
        """
        :param attr_name: The attribute name (<tag name=value">)
        :param attr_value: The attribute value (<tag name=value">)
        """
        super(HTMLAttrQuoteGeneric, self).__init__(payload, attr_value)
        self.name = attr_name
        self.value = attr_value

    def extract_code(self):
        """
        Cleanup the attribute value which is likely to contain JS code
        """
        attr_value = self.JS_PATTERN.sub('', self.value)
        return self.VB_PATTERN.sub('', attr_value)

    def can_break(self):
        #
        # Handle cases like this:
        #   <h1 style="color:blue;text-align:PAYLOAD">This is a header</h1>
        #
        if self.name == 'style':
            # TODO: Delegate the is_executable to the CSS parser
            raise NotImplementedError()

        #
        # Handle cases like this:
        #   <h1 onmouseover="do_something(PAYLOAD)">This is a header</h1>
        #
        if self.name not in self.JS_ATTRS:
            return False

        script_text = self.extract_code()

        # Delegate the is_executable to the JavaScript parser
        for js_context in get_js_context_iter(script_text, self.payload):
            # At least one of the contexts where the payload is echoed in the
            # script text needs to be escaped from
            if js_context.can_break():
                return True

        return False

    def is_executable(self):
        #
        # Handle cases like this:
        #   <h1 style="color:blue;text-align:PAYLOAD">This is a header</h1>
        #
        if self.name == 'style':
            # TODO: Delegate the is_executable to the CSS parser
            raise NotImplementedError()

        #
        # Handle cases like this:
        #   <h1 onmouseover="foo();PAYLOAD();">This is a header</h1>
        #
        if self.name not in self.JS_ATTRS:
            return False

        script_text = self.extract_code()

        # Delegate the is_executable to the JavaScript parser
        for js_context in get_js_context_iter(script_text, self.payload):
            if js_context.is_executable():
                return True

        return False


class HtmlAttrSingleQuote(HTMLAttrQuoteGeneric):
    """
    Matches <tag attr='PAYLOAD' />
    """
    ATTR_DELIMITER = "'"
    CAN_BREAK = {ATTR_DELIMITER}


class HtmlAttrDoubleQuote(HTMLAttrQuoteGeneric):
    """
    Matches <tag attr="PAYLOAD" />
    """
    ATTR_DELIMITER = '"'
    CAN_BREAK = {ATTR_DELIMITER}


class HtmlAttrBackticks(HTMLAttrQuoteGeneric):
    """
    Matches <tag attr=`PAYLOAD` />
    """
    ATTR_DELIMITER = '`'
    CAN_BREAK = {ATTR_DELIMITER}


class HtmlAttrNoQuote(HTMLAttrQuoteGeneric):
    """
    Matches <tag attr=PAYLOAD />
    """
    ATTR_DELIMITER = ''
    CAN_BREAK = {' '}