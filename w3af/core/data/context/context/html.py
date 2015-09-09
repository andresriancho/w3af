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
from w3af.core.data.context.context.base import BaseContext


class HtmlTag(BaseContext):
    """
    Matches <PAYLOAD></foo>
    """
    CAN_BREAK = {' ', '>'}


class HtmlTagClose(BaseContext):
    """
    Matches <foo></PAYLOAD>
    """
    CAN_BREAK = {' ', '>'}


class HtmlText(BaseContext):
    """
    Matches <tag attr="value">PAYLOAD</tag>
    """
    CAN_BREAK = {'<'}


class HtmlComment(BaseContext):
    """
    Matches <!-- PAYLOAD -->
    """
    CAN_BREAK = {'-', '>', '<'}


class HtmlAttr(BaseContext):
    """
    Matches <tag PAYLOAD="value" />
    """
    CAN_BREAK = {' ', '='}


class HtmlDeclaration(BaseContext):
    """
    This method is called to handle an HTML doctype declaration
    (e.g. <!DOCTYPE html>).
    """
    CAN_BREAK = {'>'}


class HtmlProcessingInstruction(BaseContext):
    """
    For example, for the processing instruction <?proc color='red'>
    """
    CAN_BREAK = {'>'}


class HTMLAttrQuoteGeneric(BaseContext):

    def __init__(self, attr_name, attr_value):
        """
        :param attr_name: The attribute name (<tag name=value">)
        :param attr_value: The attribute value (<tag name=value">)
        """
        super(HTMLAttrQuoteGeneric, self).__init__(attr_value)
        self.name = attr_name
        self.value = attr_value

    def is_executable(self):
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


class HtmlAttrDoubleQuote(HTMLAttrQuoteGeneric):
    """
    Matches <tag attr="PAYLOAD" />
    """
    ATTR_DELIMITER = '"'
    CAN_BREAK = {ATTR_DELIMITER}


class HtmlAttrBackticks(HTMLAttrQuoteGeneric):
    """
    Matches <tag attr=`PAYLOAD` />
    """
    ATTR_DELIMITER = '`'
    CAN_BREAK = {ATTR_DELIMITER}


class HtmlAttrNoQuote(HTMLAttrQuoteGeneric):
    """
    Matches <tag attr=PAYLOAD />
    """
    ATTR_DELIMITER = " "
    CAN_BREAK = {ATTR_DELIMITER}