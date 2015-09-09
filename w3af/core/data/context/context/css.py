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
from functools import wraps

from w3af.core.data.context.utils.byte_chunk import ByteChunk
from w3af.core.data.context.context.html import Context
from w3af.core.data.context.constants import QUOTE_CHARS


def crop_style(byte_chunk, context='tag'):
    if context == 'tag':
        return ByteChunk(byte_chunk.nhtml[byte_chunk.nhtml.lower().rfind('<style')+1:])
    else:
        attr_data = byte_chunk.html_attr
        if attr_data:
            return ByteChunk(byte_chunk.nhtml[attr_data[2]:])


def inside_style(meth):

    @wraps(meth)
    def wrap(self, byte_chunk):
        if byte_chunk.inside_style:
            new_bc = crop_style(byte_chunk)
            return meth(self, new_bc)

        if byte_chunk.inside_style_attr:
            new_bc = crop_style(byte_chunk, 'attr')
            return meth(self, new_bc)

        return False

    return wrap


class StyleContext(Context):

    @inside_style
    def inside_comment(self, byte_chunk):
        # We are inside /*...*/
        if byte_chunk.nhtml.rfind('/*') <= byte_chunk.nhtml.rfind('*/'):
            return False
        return True


class StyleText(StyleContext):

    def __init__(self):
        self.name = 'STYLE_TEXT'

    @inside_style
    def match(self, byte_chunk):
        if self.inside_comment(byte_chunk):
            return False

        quote_character = None

        for s in byte_chunk.nhtml:
            if s in QUOTE_CHARS:
                if quote_character and s == quote_character:
                    quote_character = None
                    continue
                elif not quote_character:
                    quote_character = s
                    continue

        if not quote_character:
            return True

        return False

    def can_break(self, payload):
        for i in ['<', '/']:
            if i not in payload:
                return False
        return True


class StyleComment(StyleContext):

    def __init__(self):
        self.name = 'STYLE_COMMENT'

    def match(self, byte_chunk):
        return self.inside_comment(byte_chunk)

    def can_break(self, payload):
        for i in ['/', '*']:
            if i not in payload:
                return False
        return True


class StyleQuote(StyleContext):

    def __init__(self):
        self.name = None
        self.quote_character = None

    @inside_style
    def match(self, byte_chunk):
        if self.inside_comment(byte_chunk):
            return False

        quote_character = None

        for s in byte_chunk.nhtml:
            if s in QUOTE_CHARS:
                if quote_character and s == quote_character:
                    quote_character = None
                    continue
                elif not quote_character:
                    quote_character = s
                    continue

        if quote_character == self.quote_character:
            return True

        return False

    def can_break(self, data):
        if self.quote_character in data:
            return True
        return False


class StyleSingleQuote(StyleQuote):

    def __init__(self):
        super(StyleSingleQuote, self).__init__()
        self.name = 'STYLE_SINGLE_QUOTE'
        self.quote_character = "'"


class StyleDoubleQuote(StyleQuote):

    def __init__(self):
        super(StyleDoubleQuote, self).__init__()
        self.name = 'STYLE_DOUBLE_QUOTE'
        self.quote_character = '"'
