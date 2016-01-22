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
from w3af.core.data.context.context.css import get_css_context_iter
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
    CAN_BREAK = {'-->'}


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

        css_text = self.get_context_content()

        for css_context in get_css_context_iter(css_text, self.payload):
            # At least one of the contexts where the payload is echoed in the
            # CSS text needs to be escaped from
            if css_context.can_break():
                return True

        return False


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

    JS_PATTERN = re.compile('^ *javascript:', re.IGNORECASE)
    VB_PATTERN = re.compile('^ *vbscript:', re.IGNORECASE)

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
        # The most common break is to simply escape the attribute string
        # delimiter and add a new attribute
        #
        if super(HTMLAttrQuoteGeneric, self).can_break():
            return True

        #
        # That didn't work, then we want to escape using different strategies
        #
        executable_handlers = [self.can_break_adding_js_protocol,
                               self.can_break_style,
                               self.can_break_js_event,
                               self.can_break_html_attr_with_js_protocol]

        for is_executable_handler in executable_handlers:
            if is_executable_handler():
                return True

        return False

    def can_break_adding_js_protocol(self):
        """
        Handle cases like this:
          <a href="PAYLOAD">

        Where the user is able to enter javascript:alert() and run arbitrary
        JS code.

        Note that after [0] was reported this method became more complex, since
        we check that the tag attribute name is one that allows/knows how to
        handle the "javascript:" protocol.

        [0] https://github.com/andresriancho/w3af/issues/13359
        """
        if self.name not in JS_EVENTS and self.name not in EXECUTABLE_ATTRS:
            return False

        if ':' not in self.payload:
            return False

        if not self.value.startswith(self.payload):
            return False

        return True

    def can_break_style(self):
        """
        Handle cases like this:
          <h1 style="color:blue;text-align:PAYLOAD">This is a header</h1>
        """
        if self.name != 'style':
            return False

        # Delegate the can_break to the CSS parser
        css_text = self.get_context_content()

        for css_context in get_css_context_iter(css_text, self.payload):
            # At least one of the contexts where the payload is echoed in the
            # CSS text needs to be escaped from
            if css_context.can_break():
                return True

        return False

    def can_break_js_event(self):
        """
        Handle cases like this:
          <h1 onmouseover="do_something(PAYLOAD)">This is a header</h1>
        """
        if self.name not in JS_EVENTS:
            return False

        # Here I replace the javascript: at the beginning, which might not
        # be there (not required by browsers) but supported in some
        script_text = self.extract_code()

        # Delegate the can_break to the JavaScript parser
        for js_context in get_js_context_iter(script_text, self.payload):
            # At least one of the contexts where the payload is echoed in the
            # script text needs to be escaped from
            if js_context.can_break():
                return True

        return False

    def can_break_html_attr_with_js_protocol(self):
        """
        Handle cases like this:
          <a href="javascript:do_something(PAYLOAD)">This is a header</a>
        """
        if self.name not in EXECUTABLE_ATTRS:
            return False

        script_text = self.extract_code()
        if self.value == script_text:
            # We get here when the attribute value DOES NOT start with
            # javascript:
            return False

        # Delegate the can_break to the JavaScript parser
        for js_context in get_js_context_iter(script_text, self.payload):
            # At least one of the contexts where the payload is echoed in the
            # script text needs to be escaped from
            if js_context.can_break():
                return True

        return False

    def is_executable_style(self):
        """
        Handle cases like this:
          <h1 style="color:blue;text-align:PAYLOAD">This is a header</h1>
        """
        if self.name != 'style':
            return False

        # Delegate the is_executable to the CSS parser
        css_text = self.get_context_content()

        for css_context in get_css_context_iter(css_text, self.payload):
            # At least one of the contexts where the payload is echoed in the
            # CSS text needs to be escaped from
            if css_context.is_executable():
                return True

        return False

    def is_executable_js_event(self):
        """
        Handle cases like this:
          <h1 onmouseover="do_something(PAYLOAD)">This is a header</h1>
        """
        if self.name not in JS_EVENTS:
            return False

        # Here I replace the javascript: at the beginning, which might not
        # be there (not required by browsers) but supported in some
        script_text = self.extract_code()

        # Delegate the can_break to the JavaScript parser
        for js_context in get_js_context_iter(script_text, self.payload):
            # At least one of the contexts where the payload is echoed in the
            # script text needs to be escaped from
            if js_context.is_executable():
                return True

        return False

    def is_executable_html_attr_with_js_protocol(self):
        """
        Handle cases like this:
          <a href="javascript:do_something(PAYLOAD)">This is a link</a>
        """
        if self.name not in EXECUTABLE_ATTRS:
            return False

        script_text = self.extract_code()
        if self.value == script_text:
            # We get here when the attribute value DOES NOT start with
            # javascript:
            return False

        # Delegate the is_executable to the JavaScript parser
        for js_context in get_js_context_iter(script_text, self.payload):
            # At least one of the contexts where the payload is echoed in the
            # script text needs to be escaped from
            if js_context.is_executable():
                return True

        return False

    def is_executable(self):
        """
        :return: True if we're in a context that we can execute without breaking
                 out.
        """
        executable_handlers = [self.is_executable_style,
                               self.is_executable_js_event,
                               self.is_executable_html_attr_with_js_protocol]

        for is_executable_handler in executable_handlers:
            if is_executable_handler():
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


ALL_CONTEXTS = [HtmlAttrNoQuote, HtmlAttrBackticks, HtmlAttrDoubleQuote,
                HtmlAttrSingleQuote, HtmlProcessingInstruction,
                HtmlDeclaration, CSSText, ScriptText, HtmlAttr, HtmlComment,
                HtmlText, HtmlTag, HtmlTagClose]