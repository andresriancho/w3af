"""
context.py

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

ATTR_DELIMITERS = {'"', '`', "'"}
JS_EVENTS = ['onclick', 'ondblclick', 'onmousedown', 'onmousemove',
            'onmouseout', 'onmouseover', 'onmouseup', 'onchange', 'onfocus', 
            'onblur', 'onscroll', 'onselect', 'onsubmit', 'onkeydown', 
            'onkeypress', 'onkeyup', 'onload', 'onunload']


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


def normalize_html(data):
    """
    Replace the < and > tags inside attribute delimiters with their encoded
    versions.

    :param data: A string with an HTML
    :return: Another string, with a modified HTML
    """
    #
    #   These constants are here because of performance
    #   https://wiki.python.org/moin/PythonSpeed/PerformanceTips
    #
    AMP_LT = '&lt;'
    AMP_GT = '&gt;'
    TAG_START = '<'
    TAG_END = '>'
    ATTR_DELIMITERS = {'"', '`', "'"}

    # Fast search and replace when more than one char needs to be searched
    repls = ("\\'", ''), ('\\"', '')
    data = reduce(lambda a, kv: a.replace(*kv), repls, data)

    # We'll use lists instead of strings for creating the result
    new_data = []
    append = new_data.append
    quote_character = None

    for s in data:
        if s in ATTR_DELIMITERS:
            if quote_character and s == quote_character:
                quote_character = None
            elif not quote_character:
                quote_character = s

        elif quote_character and s == TAG_START:
            append(AMP_LT)
            continue

        elif quote_character and s == TAG_END:
            append(AMP_GT)
            continue

        append(s)

    return ''.join(new_data)


def crop_js(byte_chunk, context='tag'):
    if context == 'tag':
        return ByteChunk(byte_chunk.nhtml[byte_chunk.nhtml.lower().rfind('<script')+1:])
    else:
        attr_data = byte_chunk.html_attr
        if attr_data:
            return ByteChunk(byte_chunk.nhtml[attr_data[2]:])

    return byte_chunk


def crop_style(byte_chunk, context='tag'):
    if context == 'tag':
        return ByteChunk(byte_chunk.nhtml[byte_chunk.nhtml.lower().rfind('<style')+1:])
    else:
        attr_data = byte_chunk.html_attr
        if attr_data:
            return ByteChunk(byte_chunk.nhtml[attr_data[2]:])


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
            if data.endswith(attr_name + '=' + self.quote_character):
                return True
        return False


class HtmlAttrSingleQuote(HtmlAttrQuote):

    def __init__(self):
        self.name = 'HTML_ATTR_SINGLE_QUOTE'
        self.quote_character = "'"


class HtmlAttrDoubleQuote(HtmlAttrQuote):

    def __init__(self):
        self.name = 'HTML_ATTR_DOUBLE_QUOTE'
        self.quote_character = '"'


class HtmlAttrBackticks(HtmlAttrQuote):

    def __init__(self):
        self.name = 'HTML_ATTR_BACKTICKS'
        self.quote_character = '`'


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


class StyleContext(Context):

    @inside_style
    def inside_comment(self, byte_chunk):
        # We are inside /*...*/
        if byte_chunk.nhtml.rfind('/*') <= byte_chunk.nhtml.rfind('*/'):
            return False
        return True


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

    def __init__(self):
        self.name = None
        self.quote_character = None

    @inside_js
    def match(self, byte_chunk):
        if self.inside_comment(byte_chunk):
            return False

        quote_character = None
        QUOTE_CHARS = {'"', "'"}

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

    def __init__(self):
        self.name = 'SCRIPT_SINGLE_QUOTE'
        self.quote_character = "'"


class ScriptDoubleQuote(ScriptQuote):

    def __init__(self):
        self.name = 'SCRIPT_DOUBLE_QUOTE'
        self.quote_character = '"'


class StyleText(StyleContext):

    def __init__(self):
        self.name = 'STYLE_TEXT'

    @inside_style
    def match(self, byte_chunk):
        if self.inside_comment(byte_chunk):
            return False

        quote_character = None
        QUOTE_CHARS = {'"', "'"}

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
        QUOTE_CHARS = {'"', "'"}

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
        self.name = 'STYLE_SINGLE_QUOTE'
        self.quote_character = "'"


class StyleDoubleQuote(StyleQuote):

    def __init__(self):
        self.name = 'STYLE_DOUBLE_QUOTE'
        self.quote_character = '"'


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


class HtmlAttrDoubleQuote2ScriptText(HtmlAttrDoubleQuote2Script, ScriptText):

    def __init__(self):
        HtmlAttrDoubleQuote2Script.__init__(self)
        self.name = 'HTML_ATTR_DOUBLE_QUOTE2SCRIPT_TEXT'

    def match(self, byte_chunk):
        if not HtmlAttrDoubleQuote2Script.match(self, byte_chunk):
            return False

        if not ScriptText._match(self, byte_chunk):
            return False

        return True

    def can_break(self, payload):
        return HtmlAttrDoubleQuote2Script.can_break(self, payload)

    def is_executable(self):
        return True


def get_contexts():
    contexts = [HtmlAttrSingleQuote(), HtmlAttrDoubleQuote(),
                HtmlAttrBackticks(), HtmlAttr(), HtmlTag(), HtmlText(),
                HtmlComment(), ScriptMultiComment(), ScriptLineComment(),
                ScriptSingleQuote(), ScriptDoubleQuote(), ScriptText(),
                StyleText(), StyleComment(), StyleSingleQuote(),
                StyleDoubleQuote()]
    #contexts.append(HtmlAttrDoubleQuote2ScriptText())
    return contexts


def get_context(data, payload):
    """
    :return: A list which contains lists of contexts
    """
    return [c for c in get_context_iter(data, payload)]


def get_context_iter(data, payload):
    """
    :return: A context iterator
    """
    chunks = data.split(payload)
    data = ''

    for chunk in chunks[:-1]:
        data += chunk

        byte_chunk = ByteChunk(data)

        for context in get_contexts():
            if context.match(byte_chunk):
                context.save(data)
                yield context


def cached_property(fun):
    """
    A memoize decorator for class properties.
    """
    @wraps(fun)
    def get(self):
        try:
            return self._cache[fun]
        except AttributeError:
            self._cache = {}
        except KeyError:
            pass
        ret = self._cache[fun] = fun(self)
        return ret

    return property(get)


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
        return (attr_name, quote_character, open_context)

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