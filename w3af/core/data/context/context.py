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

ATTR_DELIMETERS = ['"', '`', "'"]
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


def normalize_html(meth):
    
    @wraps(meth)
    def wrap(self, data):
        data = data.replace("\\'",'')
        data = data.replace('\\"','')
        new_data = ''
        quote_character = None
        for s in data:
            if s in ['"', "'", '`']:
                if quote_character and s == quote_character:
                    quote_character = None
                elif not quote_character:
                    quote_character = s
            if s == '<' and quote_character:
                s = '&lt;'
            if s == '>' and quote_character:
                s = '&gt;'
            new_data += s
        return meth(self, new_data)
    
    return wrap


def get_html_attr(data):
    attr_name = ''
    inside_name = False
    inside_value = False
    open_angle_bracket = data.rfind('<')
    quote_character = None
    open_context = None
    i = open_angle_bracket - 1

    if open_angle_bracket <= data.rfind('>'):
        return False

    for s in data[open_angle_bracket:]:
        i += 1

        if s in ATTR_DELIMETERS and not quote_character:
            quote_character = s
            if inside_value and open_context:
                open_context = i + 1
            continue
        elif s in ATTR_DELIMETERS and quote_character:
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


def _inside_js(data):
    script_index = data.lower().rfind('<script')
    
    if script_index > data.lower().rfind('</script>') and \
    data[script_index:].count('>'):
        return True
    
    return False


def _inside_style(data):
    style_index = data.lower().rfind('<style')
    
    if style_index > data.lower().rfind('</style>') and \
    data[style_index:].count('>'):
        return True
    
    return False


def _inside_html_attr(data, attrs):
    attr_data = get_html_attr(data)
    if not attr_data:
        return False
    for attr in attrs:
        if attr == attr_data[0]:
            return True
    return False


def _inside_event_attr(data):
    if _inside_html_attr(data, JS_EVENTS):
        return True
    return False


def _inside_style_attr(data):
    if _inside_html_attr(data, ['style']):
        return True
    return False


def crop_js(data, context='tag'):
    if context == 'tag':
        return data[data.lower().rfind('<script')+1:]
    else:
        attr_data = get_html_attr(data)
        if attr_data:
            return data[attr_data[2]:]
    return data


def crop_style(data, context='tag'):
    if context == 'tag':
        return data[data.lower().rfind('<style')+1:]
    else:
        attr_data = get_html_attr(data)
        if attr_data:
            return data[attr_data[2]:]


def inside_js(meth):
    def wrap(self, data):
        if _inside_js(data):
            data = crop_js(data)
            return meth(self, data)
        if _inside_event_attr(data):
            data = crop_js(data, 'attr')
            return meth(self, data)
        return False
    return wrap


def inside_style(meth):
    
    @wraps(meth)
    def wrap(self, data):
        if _inside_style(data):
            data = crop_style(data)
            return meth(self, data)
        if _inside_style_attr(data):
            data = crop_style(data, 'attr')
            return meth(self, data)
        return False
    
    return wrap


def inside_html(meth):
    
    @wraps(meth)
    def wrap(self, data):
        if _inside_js(data) or _inside_style(data):
            return False
        return meth(self, data)
    
    return wrap


class HtmlContext(Context):

    @normalize_html
    @inside_html
    def inside_comment(self, data):
        # We are inside <!--...-->
        if data.rfind('<!--') <= data.rfind('-->'):
            return False
        return True


class HtmlTag(HtmlContext):

    def __init__(self):
        self.name = 'HTML_TAG'

    @normalize_html
    @inside_html
    def match(self, data):
        if self.inside_comment(data):
            return False
        if data and data[-1] == '<':
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

    @normalize_html
    @inside_html
    def match(self, data):
        if self.inside_comment(data):
            return False
        if data.rfind('<') <= data.rfind('>'):
            return True
        return False

    def can_break(self, payload):
        if "<" in payload:
            return True
        return False


class HtmlComment(HtmlContext):

    def __init__(self):
        self.name = 'HTML_COMMENT'

    @normalize_html
    @inside_html
    def match(self, data):
        if self.inside_comment(data):
            return True
        return False

    def can_break(self, payload):
        for i in ['-', '>', '<']:
            if i not in payload:
                return False
        return True


class HtmlAttr(HtmlContext):

    def __init__(self):
        self.name = 'HTML_ATTR'

    @normalize_html
    @inside_html
    def match(self, data):
        if self.inside_comment(data):
            return False

        quote_character = None
        open_angle_bracket = data.rfind('<')
        # We are inside <...
        if open_angle_bracket <= data.rfind('>'):
            return False
        for s in data[open_angle_bracket+1:]:
            if s in ATTR_DELIMETERS:
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

    @normalize_html
    @inside_html
    def match(self, data):
        return self._match(data)
    
    def _match(self, data):
        if self.inside_comment(data):
            return False
        quote_character = None
        open_angle_bracket = data.rfind('<')
        # We are inside <...
        if open_angle_bracket <= data.rfind('>'):
            return False
        for s in data[open_angle_bracket+1:]:
            if s in ATTR_DELIMETERS:
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
    
    @normalize_html
    @inside_js
    def inside_comment(self, data):
        return (self._inside_multi_comment(data) or self._inside_line_comment(data))

    @normalize_html
    @inside_js
    def _inside_multi_comment(self, data):
        # We are inside /*...
        if data.rfind('/*') <= data.rfind('*/'):
            return False
        return True

    @normalize_html
    @inside_js
    def _inside_line_comment(self, data):
        last_line = data.split('\n')[-1].strip()
        if last_line.find('//') == 0:
            return True
        return False


class StyleContext(Context):

    @normalize_html
    @inside_style
    def inside_comment(self, data):
        # We are inside /*...*/
        if data.rfind('/*') <= data.rfind('*/'):
            return False
        return True


class ScriptMultiComment(ScriptContext):

    def __init__(self):
        self.name = 'SCRIPT_MULTI_COMMENT'

    def match(self, data):
        return self._inside_multi_comment(data)

    def can_break(self, payload):
        for i in ['/', '*']:
            if i not in payload:
                return False
        return True


class ScriptLineComment(ScriptContext):

    def __init__(self):
        self.name = 'SCRIPT_LINE_COMMENT'

    def match(self, data):
        return self._inside_line_comment(data)

    def can_break(self, payload):
        for i in ['\n']:
            if i not in payload:
                return False
        return True


class ScriptQuote(ScriptContext):

    def __init__(self):
        self.name = None
        self.quote_character = None

    @normalize_html
    @inside_js
    def match(self, data):
        if self.inside_comment(data):
            return False
        quote_character = None
        for s in data:
            if s in ['"', "'"]:
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

    @normalize_html
    @inside_style
    def match(self, data):
        if self.inside_comment(data):
            return False
        quote_character = None
        for s in data:
            if s in ['"', "'"]:
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

    @normalize_html
    @inside_js
    def match(self, data):
        return self._match(data)

    def _match(self, data):
        if self.inside_comment(data):
            return False
        return True

        quote_character = None
        for s in data:
            if s in ['"', "'"]:
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

    def is_executable(self):
        return True


class StyleComment(StyleContext):

    def __init__(self):
        self.name = 'STYLE_COMMENT'

    def match(self, data): 
        return self.inside_comment(data)

    def can_break(self, data):
        for i in ['/', '*']:
            if i not in data:
                return False
        return True


class StyleQuote(StyleContext):

    def __init__(self):
        self.name = None
        self.quote_character = None

    @normalize_html
    @inside_style
    def match(self, data):
        if self.inside_comment(data):
            return False
        quote_character = None
        for s in data:
            if s in ['"', "'"]:
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

    @normalize_html
    @inside_html
    def match(self, data):
        if not HtmlAttrDoubleQuote._match(self, data):
            return False
        data = data.lower().replace(' ', '')
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

    def match(self, data):
        if not HtmlAttrDoubleQuote2Script.match(self, data):
            return False
        if not ScriptText._match(self, data):
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
    tmp = ''

    for chunk in chunks[:-1]:
        tmp += chunk

        for context in get_contexts():
            if context.match(tmp):
                context.save(tmp)
                yield context

