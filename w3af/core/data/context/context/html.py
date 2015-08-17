"""
finders.py

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
from functools import wraps

from w3af.core.data.context.constants import ATTR_DELIMITERS, JS_EVENTS


class Context(object):
    name = ''
    data = ''

    def get_name(self):
        return self.name

    def is_executable(self):
        return False

    def can_break(self, payload):
        raise NotImplementedError('can_break() should be implemented')

    def match(self, data):
        raise NotImplementedError('match() should be implemented')

    def inside_comment(self, data):
        raise NotImplementedError('inside_comment() should be implemented')

    def save(self, data):
        self.data = data


def inside_html(meth):

    @wraps(meth)
    def wrap(self, byte_chunk):
        if not byte_chunk.inside_html:
            return False
        return meth(self, byte_chunk)

    return wrap


def not_html_comment(meth):

    @wraps(meth)
    def wrap(self, byte_chunk):
        if byte_chunk.inside_comment:
            return False
        return meth(self, byte_chunk)

    return wrap


class HtmlContext(Context):
    pass


class HtmlTag(HtmlContext):

    def __init__(self):
        self.name = 'HTML_TAG'

    @inside_html
    @not_html_comment
    def match(self, byte_chunk):
        if byte_chunk.nhtml and byte_chunk.nhtml[-1] == '<':
            return True

        return False

    def can_break(self, payload):
        for i in [' ', '>']:
            if i in payload:
                return True
        return False


class HtmlText(HtmlContext):

    def __init__(self):
        self.name = 'HTML_TEXT'

    @inside_html
    @not_html_comment
    def match(self, byte_chunk):
        if byte_chunk.nhtml.rfind('<') <= byte_chunk.nhtml.rfind('>'):
            return True
        return False

    def can_break(self, payload):
        if "<" in payload:
            return True
        return False


class HtmlComment(HtmlContext):

    def __init__(self):
        self.name = 'HTML_COMMENT'

    @inside_html
    def match(self, byte_chunk):
        return byte_chunk.inside_comment

    def can_break(self, payload):
        for i in ['-', '>', '<']:
            if i not in payload:
                return False
        return True


class HtmlAttr(HtmlContext):

    def __init__(self):
        self.name = 'HTML_ATTR'

    @inside_html
    @not_html_comment
    def match(self, byte_chunk):
        quote_character = None
        data = byte_chunk.nhtml

        open_angle_bracket = data.rfind('<')

        # We are inside <...
        if open_angle_bracket <= data.rfind('>'):
            return False

        for s in data[open_angle_bracket+1:]:
            if s in ATTR_DELIMITERS:
                if quote_character and s == quote_character:
                    quote_character = None
                    continue
                elif not quote_character:
                    quote_character = s
                    continue

        if not quote_character and len(data[open_angle_bracket+1:]):
            return True

        return False

    def can_break(self, payload):
        for i in [' ', '=']:
            if i not in payload:
                return False
        return True


class HtmlAttrQuote(HtmlAttr):

    html_url_attrs = ['href', 'src']

    def __init__(self):
        super(HtmlAttrQuote, self).__init__()
        self.name = None
        self.quote_character = None

    @inside_html
    def match(self, byte_chunk):
        return self._match(byte_chunk)

    @not_html_comment
    def _match(self, byte_chunk):
        quote_character = None
        data = byte_chunk.nhtml

        open_angle_bracket = data.rfind('<')

        # We are inside <...
        if open_angle_bracket <= data.rfind('>'):
            return False

        for s in data[open_angle_bracket+1:]:
            if s in ATTR_DELIMITERS:
                if quote_character and s == quote_character:
                    quote_character = None
                    continue
                elif not quote_character:
                    quote_character = s
                    continue

        # This translates to: "HTML string opener an attr delimiter which was
        # never closed, so we're inside an HTML tag attribute"
        if quote_character == self.quote_character:
            return True

        return False

    def can_break(self, payload):
        if self.quote_character in payload:
            return True
        return False

    def is_executable(self):
        data = self.data.lower().replace(' ', '')
        for attr_name in (self.html_url_attrs + JS_EVENTS):
            # Does the data look like this? <frame src="
            if data.endswith(attr_name + '=' + self.quote_character):
                return True
        return False


class HtmlAttrSingleQuote(HtmlAttrQuote):

    def __init__(self):
        super(HtmlAttrSingleQuote, self).__init__()
        self.name = 'HTML_ATTR_SINGLE_QUOTE'
        self.quote_character = "'"


class HtmlAttrDoubleQuote(HtmlAttrQuote):

    def __init__(self):
        super(HtmlAttrDoubleQuote, self).__init__()
        self.name = 'HTML_ATTR_DOUBLE_QUOTE'
        self.quote_character = '"'


class HtmlAttrBackticks(HtmlAttrQuote):

    def __init__(self):
        super(HtmlAttrBackticks, self).__init__()
        self.name = 'HTML_ATTR_BACKTICKS'
        self.quote_character = '`'


class HtmlAttrDoubleQuote2Script(HtmlAttrDoubleQuote):

    def __init__(self):
        HtmlAttrDoubleQuote.__init__(self)
        self.name = 'HTML_ATTR_DOUBLE_QUOTE2SCRIPT'

    @inside_html
    def match(self, byte_chunk):
        if not HtmlAttrDoubleQuote._match(self, byte_chunk):
            return False

        data = byte_chunk.nhtml.lower().replace(' ', '')

        for attr_name in JS_EVENTS:
            if data.endswith(attr_name + '=' + self.quote_character):
                break
        else:
            return False
        #        data = data.lower().replace('&quote;', '"')
        return True
