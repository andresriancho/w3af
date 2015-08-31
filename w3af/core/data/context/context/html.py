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
from w3af.core.data.context.constants import ATTR_DELIMITERS
from w3af.core.data.context.context.base import BaseContext


class HtmlTag(BaseContext):
    """
    Matches <PAYLOAD></foo>
    """
    CAN_BREAK = {' ', '>'}

    @staticmethod
    def match(html):
        # If it ends with a "<" it means that the payload was right after the
        # tag start character (<)
        if html and html.endswith('<'):
            return True

        return False


class HtmlTagClose(BaseContext):
    """
    Matches <foo></PAYLOAD>
    """
    CAN_BREAK = {' ', '>'}

    @staticmethod
    def match(html):
        # If it ends with a "</" it means that the payload was right after the
        # tag start character (</)
        if html and html.endswith('</'):
            return True

        return False


class HtmlText(BaseContext):
    """
    Matches <tag attr="value">PAYLOAD</tag>
    """
    CAN_BREAK = {'<'}

    @staticmethod
    def match(html):
        # Special case where the only thing in the HTML is the payload/the
        # HTML starts with the payload
        if not html:
            return True

        # The other cases where there is a tag soup
        return BaseContext.is_inside_context(html, '>', '<')


class HtmlComment(BaseContext):
    """
    Matches <!-- PAYLOAD -->
    """

    CAN_BREAK = {'-', '>', '<'}

    @staticmethod
    def match(html):
        return BaseContext.is_inside_html_comment(html)


class HtmlAttr(BaseContext):
    """
    Matches <tag PAYLOAD="value" />
    """

    CAN_BREAK = {' ', '='}

    @staticmethod
    def match(html):
        if not BaseContext.is_inside_context(html, '<', '>'):
            # We're not inside the tag context, so there is no way we're inside
            # any tag attribute name
            return False

        if BaseContext.is_inside_context(html, '</', '>'):
            # Nothing to be done inside a closing tag attr
            return False

        quote_character = None

        open_angle_bracket = html.rfind('<')

        for s in html[open_angle_bracket+1:]:
            if s in ATTR_DELIMITERS:
                if quote_character and s == quote_character:
                    quote_character = None
                    continue
                elif not quote_character:
                    quote_character = s
                    continue

        if not quote_character and len(html[open_angle_bracket+1:]):
            return True

        return False


class HTMLAttrQuoteGeneric(HtmlAttr):

    @staticmethod
    def _match(html, attr_delimiter):
        context_starts = ['<', attr_delimiter]
        context_ends = ['>', attr_delimiter]

        # This translates to: "HTML string opener an attr delimiter which was
        # never closed, so we're inside an HTML tag attribute"
        if BaseContext.is_inside_nested_contexts(html,
                                                 context_starts,
                                                 context_ends):
            return True

        return False

    @staticmethod
    def is_executable(html):
        # TODO: Here I need to check if the tag name is in XXX and the attr
        # name is in YYY, then send the contents of the attribute name to
        # the JavaScript parser and delegate the "is_executable" to that code
        raise NotImplementedError


class HtmlAttrSingleQuote(HTMLAttrQuoteGeneric):
    """
    Matches <tag attr='PAYLOAD' />
    """

    ATTR_DELIMITER = "'"
    CAN_BREAK = {ATTR_DELIMITER}

    @staticmethod
    def match(html):
        return HTMLAttrQuoteGeneric._match(html,
                                           HtmlAttrSingleQuote.ATTR_DELIMITER)


class HtmlAttrDoubleQuote(HTMLAttrQuoteGeneric):
    """
    Matches <tag attr="PAYLOAD" />
    """

    ATTR_DELIMITER = '"'
    CAN_BREAK = {ATTR_DELIMITER}

    @staticmethod
    def match(html):
        return HTMLAttrQuoteGeneric._match(html,
                                           HtmlAttrDoubleQuote.ATTR_DELIMITER)


class HtmlAttrBackticks(HTMLAttrQuoteGeneric):
    """
    Matches <tag attr=`PAYLOAD` />
    """

    ATTR_DELIMITER = '`'
    CAN_BREAK = {ATTR_DELIMITER}

    @staticmethod
    def match(html):
        return HTMLAttrQuoteGeneric._match(html,
                                           HtmlAttrBackticks.ATTR_DELIMITER)
