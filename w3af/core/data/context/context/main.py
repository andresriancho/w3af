"""
main.py

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
from HTMLParser import HTMLParser, HTMLParseError

from w3af.core.data.context.constants import CONTEXT_DETECTOR
from .html import (HtmlAttrSingleQuote, HtmlAttrDoubleQuote,
                   HtmlAttrBackticks, HtmlAttr, HtmlTag, HtmlText,
                   HtmlComment, HtmlTagClose, HtmlAttrNoQuote,
                   HtmlDeclaration, HtmlProcessingInstruction,
                   CSSText, ScriptText)


def get_context(data, payload):
    """
    :return: A list which contains lists of all contexts where the payload lives
    """
    return [c for c in get_context_iter(data, payload)]


def get_context_iter(data, payload):
    """
    :param data: The HTML where the payload might be in
    :param payload: The payload as sent to the web application

    :return: A context iterator

    :see: https://github.com/andresriancho/w3af/issues/37
    """
    # We don't care if the payload we sent was processed with something like
    # payload.title() , payload.upper() or payload.lower() and then pushed
    # into the output.
    #
    # Remember that some payloads we use do contain letters which might be
    # affected by those filters; we don't just send the special characters.
    payload = payload.lower()
    data = data.lower()

    if payload not in data:
        return

    # We replace the "context breaking payload" with an innocent string
    data = data.replace(payload, CONTEXT_DETECTOR)

    # Parse!
    context_detector = ContextDetectorHTMLParser(payload)
    try:
        context_detector.feed(data)
    except HTMLParseError:
        # HTMLParser is able to handle broken markup, but in some cases it might
        # raise this exception when it encounters an error while parsing.
        return

    for context in context_detector.contexts:
        yield context

    # Clear
    context_detector.close()


class ContextDetectorHTMLParser(HTMLParser):

    def __init__(self, payload):
        HTMLParser.__init__(self)
        self.payload = payload
        self.contexts = []
        self.current_tag = None
        self.noscript_parent = False

    def untidy(self, content):
        return content.replace(CONTEXT_DETECTOR, self.payload)
    
    def append_context(self, context):
        # We just ignore all the contexts which are inside <noscript>
        if self.noscript_parent:
            return
        
        self.contexts.append(context)

    def handle_starttag(self, tag, attrs):
        """
        Find the payload in:
            * Tag name
            * Tag attribute name
            * Tag attribute value (double, single and backtick quotes)

        :param tag: The tag name
        :param attrs: A list of tuples with attributes
        :return: None, we save the contexts where the payloads were found to
                 the "contexts" class attribute
        """
        self.current_tag = tag

        if tag == 'noscript':
            self.noscript_parent = True

        if CONTEXT_DETECTOR in tag:
            self.append_context(HtmlTag(self.payload, self.untidy(tag)))

        for attr_name, attr_value in attrs:
            if CONTEXT_DETECTOR in attr_name:
                self.append_context(HtmlAttr(self.payload,
                                             self.untidy(attr_name)))

            if attr_value and CONTEXT_DETECTOR in attr_value:
                context = self.get_attr_value_context(attr_name, attr_value)
                if context is not None:
                    self.append_context(context)

    handle_startendtag = handle_starttag

    def get_attr_value_context(self, attr_name, attr_value):
        """
        Use HTMLParser.get_starttag_text to find which quote delimiter was used
        in this tag.

        :return: The context instance, one of:
                    * HtmlAttrDoubleQuote
                    * HtmlAttrSingleQuote
                    * HtmlAttrBackticks
        """
        # Get the raw text string that triggered this parse event
        full_tag_text = self.get_starttag_text()

        # Since it's the raw text value and the attr_value was unescaped, we
        # need to unescape it too to be able to compare them
        full_tag_text = self.unescape(full_tag_text)

        # Analyze the generic cases
        all_contexts = [HtmlAttrDoubleQuote,
                        HtmlAttrSingleQuote]

        for context_klass in all_contexts:
            attr_match = '%s%s%s' % (context_klass.ATTR_DELIMITER,
                                     attr_value,
                                     context_klass.ATTR_DELIMITER)
            if attr_match in full_tag_text:
                return context_klass(self.payload,
                                     attr_name,
                                     self.untidy(attr_value))

        # Special case for HtmlAttrBackticks
        if attr_value.startswith(HtmlAttrBackticks.ATTR_DELIMITER) and \
           attr_value.endswith(HtmlAttrBackticks.ATTR_DELIMITER):
            return HtmlAttrBackticks(self.payload,
                                     attr_name,
                                     self.untidy(attr_value))

        # And if we don't have any quotes... then...
        return HtmlAttrNoQuote(self.payload,
                               attr_name,
                               self.untidy(attr_value))

    def handle_endtag(self, tag):
        if tag == 'noscript':
            self.noscript_parent = False

        if CONTEXT_DETECTOR in tag:
            self.append_context(HtmlTagClose(self.payload, self.untidy(tag)))

    def handle_data(self, text_data):
        if CONTEXT_DETECTOR not in text_data:
            return

        if self.current_tag == 'script':
            self.append_context(ScriptText(self.payload,
                                           self.untidy(text_data)))

        elif self.current_tag == 'style':
            self.append_context(CSSText(self.payload,
                                        self.untidy(text_data)))

        elif CONTEXT_DETECTOR in text_data:
            self.append_context(HtmlText(self.payload,
                                         self.untidy(text_data)))

    def handle_comment(self, comment_text):
        if CONTEXT_DETECTOR in comment_text:
            self.append_context(HtmlComment(self.payload,
                                            self.untidy(comment_text)))

    def handle_decl(self, data):
        if CONTEXT_DETECTOR in data:
            self.append_context(HtmlDeclaration(self.payload,
                                                self.untidy(data)))

    def handle_pi(self, data):
        if CONTEXT_DETECTOR in data:
            self.append_context(HtmlProcessingInstruction(self.payload,
                                                          self.untidy(data)))
