
def inside_js(meth):
    """
    This is a rather complex decorator that will modify the ByteChunk according
    to various situations.

        * <script>...</script>
        * <a onmouseover="...">
        * <a href="javascript:...">

    See the inline docs for more information on the cases and how they are
    handled.

    :param meth: The method to decorate
    :return: False if we're not inside JavaScript context, else the result of
             calling the wrapped method with the modified ByteChunk (modified
             as documented above)
    """

    def wrap(self, byte_chunk):
        if byte_chunk.inside_js:
            # The payload is inside a <script> tag, get the script contents
            # and process them in the wrapped method
            #
            # This is the case where the byte chunk contains something like:
            #
            #       <script>
            #           hello();
            #           world();
            #           var a = '
            #
            # And the payload is inside the variable contents
            #
            # TODO: What about cases like <script type="text/javascript"> ?
            #       I believe I'm sending type="text/javascript" as part of the
            #       script source chunk
            script_start = byte_chunk.nhtml.lower().rfind('<script')
            script_source_chunk = ByteChunk(byte_chunk.nhtml[script_start+1:])
            return meth(self, script_source_chunk)

        if byte_chunk.inside_event_attr:
            # This is the case where the we have a JS event in the tag and the
            # payload is inside it. The HTML looks like:
            #
            #       <a onmouseover="foo();PAYLOAD">
            #
            # And the byte chunk looks like:
            #
            #       <a onmouseover="foo();
            #
            # Note that in this case the developer is not required to add the
            # javascript: handler to the onmouseover attribute value (see case
            # below for an example of javascript:)

            # Note that attr_data can't be False because we already checked that
            # in inside_event_attr
            attr_data = byte_chunk.html_attr

            # What this does is to find the attribute name (onmouseover)
            # add + 2 to the index to account for the = and (single|double)
            # quote (onmouseover=" or onmouseover=') and return the rest.
            #
            # Basically if we start with a byte chunk containing:
            #
            #   <a onmouseover="foo();
            #
            # We create a new byte chunk with foo();
            attr_script_chunk = ByteChunk(byte_chunk.nhtml[attr_data[2]:])
            return meth(self, attr_script_chunk)



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


class TagAttributeDoubleQuoteScript(HtmlAttrDoubleQuote):
    """
    <a href="javascript:foo();PAYLOAD">...</a>
    """
    def match(self, byte_chunk):
        if not byte_chunk.inside_js_handler_attr:
            return False

        # This is the case where we have an href / src attribute which
        # contains a "javascript:" target which will run JS in the browser.
        # If the HTML looks like this:
        #
        #       <a href="javascript:foo();PAYLOAD">...</a>
        #
        # The byte chunk would look like
        #
        #       <a href="javascript:foo();
        #
        # And we want to create a new byte chunk that will send the JS code
        # to the analyzer, containing:
        #
        #       foo();

        # Note that attr_data can't be False because we already checked that
        # in inside_event_attr
        attr_data = byte_chunk.html_attr
        attr_name, quote_character, open_context = attr_data
        attr_value = byte_chunk.nhtml[open_context:]

        javascript = 'javascript:'
        vbscript = 'vbscript:'
        client_side_code = ''

        if attr_value.lower().startswith(javascript):
            client_side_code = attr_value[len(javascript):]

        elif attr_value.lower().startswith(vbscript):
            client_side_code = attr_value[len(vbscript):]

        # What this does is to find the attribute name (href|src)
        # add + 2 to the index to account for the = and (single|double)
        # quote (href=" or href='), from there find the javascript: and
        # and return the script after ":"
        attr_script_chunk = ByteChunk(client_side_code)
        return True

    def is_executable(self):
        return True

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
