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
from w3af.core.data.context.utils import encode_payloads, decode_payloads
from .html import (HtmlAttrSingleQuote, HtmlAttrDoubleQuote,
                   HtmlAttrBackticks, HtmlAttr, HtmlTag, HtmlRawText,
                   HtmlText, HtmlComment, HtmlTagClose, HtmlAttrNoQuote,
                   HtmlDeclaration, HtmlProcessingInstruction,
                   CSSText, ScriptText)


def get_context(data, boundary):
    """
    :param data: The HTML where the payload might be in
    :param boundary: The payload border as sent to the web application

    :return: A list which contains lists of all contexts where the payload lives
    """
    return [c for c in get_context_iter(data, boundary)]


def get_context_iter(data, boundary):
    """
    :param data: The HTML where the payload might be in
    :param boundary: The payload border as sent to the web application

    :return: A context iterator

    :see: https://github.com/andresriancho/w3af/issues/37
    """
    # We don't care if the payload we sent was processed with something like
    # payload.title() , payload.upper() or payload.lower() and then pushed
    # into the output.
    #
    # Remember that some payloads we use do contain letters which might be
    # affected by those filters; we don't just send the special characters.

    data = data.lower()
    for bound in boundary:
        if bound not in data:
            return

    # We replace the "context breaking payload" with an innocent string
    data = encode_payloads(boundary, data)

    # Parse!
    context_detector = ContextDetectorHTMLParser(boundary)
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

    RAW_TEXT_TAG = {
        'title',
        'textarea',
        'plaintext',
        'xmp',
        'listing'
    }

    def __init__(self, bound):
        HTMLParser.__init__(self)
        self.bound = bound
        self.contexts = []
        self.current_tag = None
        self.noscript_parent = False

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
            payloads, context_content = decode_payloads(tag)
            self.append_context(HtmlTag(payloads.pop(),
                                        context_content,
                                        self.bound))

        for attr_name, attr_value in attrs:
            if CONTEXT_DETECTOR in attr_name:
                payloads, context_content = decode_payloads(attr_name)
                self.append_context(HtmlAttr(payloads.pop(),
                                             context_content,
                                             self.bound))

            if attr_value and CONTEXT_DETECTOR in attr_value:
                contexts = self.get_attr_value_context(attr_name, attr_value)
                for context in contexts:
                    self.append_context(context)

    handle_startendtag = handle_starttag

    def get_attr_value_context(self, attr_name, attr_value):
        """
        Use HTMLParser.get_starttag_text to find which quote delimiter was used
        in this tag.

        :param attr_name: The tag attribute name
        :param attr_value:  The tag attribute value

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
        attr_context_klass = None

        payloads, context_content = decode_payloads(attr_value)
        # Since the attr_value was unescaped, we need to unescape payloads in
        # context_content too to be able to analyse
        for payload in payloads:
            un_payload = self.unescape(payload)
            context_content = context_content.replace(payload, un_payload)

        for context_klass in all_contexts:
            attr_match = '%s%s%s' % (context_klass.ATTR_DELIMITER,
                                     attr_value,
                                     context_klass.ATTR_DELIMITER)
            if attr_match in full_tag_text:
                attr_context_klass = context_klass
                break

        # Special case for HtmlAttrBackticks
        if not attr_context_klass and \
           attr_value.startswith(HtmlAttrBackticks.ATTR_DELIMITER) and \
           attr_value.endswith(HtmlAttrBackticks.ATTR_DELIMITER):
            attr_context_klass = HtmlAttrBackticks

        # And if we don't have any quotes... then...
        if not attr_context_klass:
            attr_context_klass = HtmlAttrNoQuote

        for payload in payloads:
            yield attr_context_klass(
                payload,
                attr_name,
                context_content,
                self.bound)

    def handle_endtag(self, tag):
        if tag == 'noscript':
            self.noscript_parent = False

        if CONTEXT_DETECTOR not in tag:
            return

        payloads, context_content = decode_payloads(tag)
        for payload in payloads:
            self.append_context(HtmlTagClose(payload,
                                             context_content,
                                             self.bound))

    def handle_data(self, text_data):
        if CONTEXT_DETECTOR not in text_data:
            return

        payloads, context_content = decode_payloads(text_data)

        if self.current_tag == 'script':
            self.append_context(ScriptText(payloads,
                                           context_content,
                                           self.bound))

        elif self.current_tag == 'style':
            self.append_context(CSSText(payloads,
                                        context_content,
                                        self.bound))

        elif CONTEXT_DETECTOR in text_data:
            for payload in payloads:
                if self.current_tag in self.RAW_TEXT_TAG:
                    self.append_context(HtmlRawText(payload,
                                                    context_content,
                                                    self.bound))
                else:
                    self.append_context(HtmlText(payload,
                                                 context_content,
                                                 self.bound))

    def handle_comment(self, comment_text):
        if CONTEXT_DETECTOR not in comment_text:
            return

        payloads, context_content = decode_payloads(comment_text)
        for payload in payloads:
            self.append_context(HtmlComment(payload,
                                            context_content,
                                            self.bound))

    def handle_decl(self, data):
        if CONTEXT_DETECTOR not in data:
            return

        payloads, context_content = decode_payloads(data)
        for payload in payloads:
            self.append_context(HtmlDeclaration(payload,
                                                context_content,
                                                self.bound))

    def handle_pi(self, data):
        if CONTEXT_DETECTOR not in data:
            return

        payloads, context_content = decode_payloads(data)
        for payload in payloads:
            self.append_context(HtmlProcessingInstruction(payload,
                                                          context_content,
                                                          self.bound))
