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
from w3af.core.data.context.utils.byte_chunk import ByteChunk
from w3af.core.data.context.context.html import Context
from w3af.core.data.context.constants import QUOTE_CHARS


def crop_js(byte_chunk, context='tag'):
    if context == 'tag':
        return ByteChunk(byte_chunk.nhtml[byte_chunk.nhtml.lower().rfind('<script')+1:])
    else:
        attr_data = byte_chunk.html_attr
        if attr_data:
            return ByteChunk(byte_chunk.nhtml[attr_data[2]:])

    return byte_chunk


def inside_js(meth):

    def wrap(self, byte_chunk):
        if byte_chunk.inside_js:
            new_bc = crop_js(byte_chunk)
            return meth(self, new_bc)

        if byte_chunk.inside_event_attr:
            new_bc = crop_js(byte_chunk, 'attr')
            return meth(self, new_bc)

        return False
    return wrap


class ScriptContext(Context):

    @inside_js
    def inside_comment(self, byte_chunk):
        return (self._inside_multi_comment(byte_chunk) or
                self._inside_line_comment(byte_chunk))

    @inside_js
    def _inside_multi_comment(self, byte_chunk):
        # We are inside /*...
        if byte_chunk.nhtml.rfind('/*') <= byte_chunk.nhtml.rfind('*/'):
            return False
        return True

    @inside_js
    def _inside_line_comment(self, byte_chunk):
        last_line = byte_chunk.nhtml.split('\n')[-1].strip()
        if last_line.find('//') == 0:
            return True
        return False


class ScriptMultiComment(ScriptContext):

    def __init__(self):
        self.name = 'SCRIPT_MULTI_COMMENT'

    def match(self, byte_chunk):
        return self._inside_multi_comment(byte_chunk)

    def can_break(self, payload):
        for i in ['/', '*']:
            if i not in payload:
                return False
        return True


class ScriptLineComment(ScriptContext):

    def __init__(self):
        self.name = 'SCRIPT_LINE_COMMENT'

    def match(self, byte_chunk):
        return self._inside_line_comment(byte_chunk)

    def can_break(self, payload):
        for i in ['\n']:
            if i not in payload:
                return False
        return True


class ScriptQuote(ScriptContext):
    """
    <script>
        var a = "PAYLOAD";
        var b = 'PAYLOAD';
    </script>
    """
    def __init__(self):
        self.name = None
        self.quote_character = None

    @inside_js
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

    def can_break(self, payload):
        if self.quote_character in payload:
            return True
        return False


class ScriptSingleQuote(ScriptQuote):
    """
    <script>
        var b = 'PAYLOAD';
    </script>
    """
    def __init__(self):
        super(ScriptSingleQuote, self).__init__()
        self.name = 'SCRIPT_SINGLE_QUOTE'
        self.quote_character = "'"


class ScriptDoubleQuote(ScriptQuote):
    """
    <script>
        var a = "PAYLOAD";
    </script>
    """
    def __init__(self):
        super(ScriptDoubleQuote, self).__init__()
        self.name = 'SCRIPT_DOUBLE_QUOTE'
        self.quote_character = '"'


class ScriptText(ScriptContext):

    def __init__(self):
        self.name = 'SCRIPT_TEXT'

    @inside_js
    def match(self, byte_chunk):
        return self._match(byte_chunk)

    def _match(self, byte_chunk):
        if self.inside_comment(byte_chunk):
            return False
        return True

    def can_break(self, payload):
        for i in ['<', '/']:
            if i not in payload:
                return False
        return True

    def is_executable(self):
        return True