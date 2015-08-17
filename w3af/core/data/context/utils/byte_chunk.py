"""
byte_chunk.py

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
from w3af.core.data.context.utils.normalize import normalize_html
from w3af.core.data.context.constants import ATTR_DELIMITERS, JS_EVENTS
from w3af.core.controllers.misc.decorators import cached_property


class ByteChunk(object):
    """
    This is a very simple class that holds a piece of HTML, and attributes which
    are added by the different contexts as it is processed.

    For example, the ByteChunk starts with a set of empty attributes and then
    after being processed by a context if might end up with a "inside_html"
    attribute. This means that the next Context will not have to process the
    inside_html decorator again, it just needs to ask if it has the attr in the
    set.
    """
    def __init__(self, data):
        self.attributes = dict()
        self.data = data

    def __repr__(self):
        return '<ByteChunk for "%s...">' % self.data[-25:]

    @cached_property
    def nhtml(self):
        return normalize_html(self.data)

    @cached_property
    def inside_html(self):
        if self.inside_js or self.inside_style:
            return False

        return True

    @cached_property
    def inside_comment(self):
        if not self.inside_html:
            return False

        # We are inside <!--...-->
        if self.nhtml.rfind('<!--') <= self.nhtml.rfind('-->'):
            return False

        return True

    @cached_property
    def html_attr(self):
        attr_name = ''
        inside_name = False
        inside_value = False
        data = self.nhtml
        open_angle_bracket = data.rfind('<')
        quote_character = None
        open_context = None
        i = open_angle_bracket - 1

        if open_angle_bracket <= data.rfind('>'):
            return False

        for s in data[open_angle_bracket:]:
            i += 1

            if s in ATTR_DELIMITERS and not quote_character:
                quote_character = s
                if inside_value and open_context:
                    open_context = i + 1
                continue
            elif s in ATTR_DELIMITERS and quote_character:
                quote_character = None
                inside_value = False
                open_context = None
                continue

            if quote_character:
                continue

            if s == ' ':
                inside_name = True
                inside_value = False
                attr_name = ''
                continue

            if s == '=':
                inside_name = False
                inside_value = True
                open_context = i + 1
                continue

            if inside_name:
                attr_name += s
        attr_name = attr_name.lower()
        return attr_name, quote_character, open_context

    @cached_property
    def inside_js(self):
        script_index = self.nhtml.lower().rfind('<script')

        if script_index > self.nhtml.lower().rfind('</script>') and \
        self.nhtml[script_index:].count('>'):
            return True

        return False

    @cached_property
    def inside_style(self):
        style_index = self.nhtml.lower().rfind('<style')

        if style_index > self.nhtml.lower().rfind('</style>') and \
        self.nhtml[style_index:].count('>'):
            return True

        return False

    def inside_html_attr(self, attrs):
        attr_data = self.html_attr
        if not attr_data:
            return False

        for attr in attrs:
            if attr == attr_data[0]:
                return True

        return False

    @cached_property
    def inside_event_attr(self):
        if self.inside_html_attr(JS_EVENTS):
            return True
        return False

    @cached_property
    def inside_style_attr(self):
        if self.inside_html_attr(['style']):
            return True
        return False
