"""
document_parser.py

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
from w3af.core.data.parsers.html import HTMLParser
from w3af.core.data.parsers.pdf import PDFParser
from w3af.core.data.parsers.swf import SWFParser
from w3af.core.data.parsers.wml_parser import WMLParser
from w3af.core.data.parsers.javascript import JavaScriptParser

from w3af.core.controllers.exceptions import BaseFrameworkException


class DocumentParser(object):
    """
    This class is a document parser.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    PARSERS = [WMLParser, HTMLParser, JavaScriptParser, PDFParser, SWFParser]

    def __init__(self, http_resp):

        # Create the proper parser instance, please note that
        # the order in which we ask for the type is not random,
        # first we discard the images which account for a great
        # % of the URLs in a site, then we ask for WML which is
        # a very specific thing to match, then we try text or HTML
        # which is very generic (if we would have exchanged these two
        # we would have never got to WML), etc.
        if http_resp.is_image():
            msg = 'There is no parser for images.'
            raise BaseFrameworkException(msg)

        for parser in self.PARSERS:
            if parser.can_parse(http_resp):
                self._parser = parser(http_resp)
                break
        else:
            msg = 'There is no parser for "%s".' % http_resp.get_url()
            raise BaseFrameworkException(msg)

    def get_forms(self):
        """
        :return: A list of forms.
        """
        return self._parser.get_forms()

    def get_references(self):
        """
        :return: A tuple that contains two lists:
            * URL objects extracted through parsing,
            * URL objects extracted through RE matching

        Returned in two separate lists because the first ones
        are much more accurate and they might deserve a different
        treatment.
        """
        return self._parser.get_references()

    def get_references_of_tag(self, tag):
        """
        :param tag: A tag object.
        :return: A list of references related to the tag that is passed as
                 parameter.
        """
        return self._parser.get_references_of_tag(tag)

    def get_emails(self, domain=None):
        """
        :param domain: Indicates what email addresses I want to retrieve:
                       "*@domain".
        :return: A list of email accounts that are inside the document.
        """
        return self._parser.get_emails(domain)

    def get_comments(self):
        """
        :return: A list of comments.
        """
        return self._parser.get_comments()

    def get_meta_redir(self):
        """
        :return: A list of the meta redirection tags.
        """
        return self._parser.get_meta_redir()

    def get_meta_tags(self):
        """
        :return: A list of all meta tags.
        """
        return self._parser.get_meta_tags()


def document_parser_factory(http_resp):
    return DocumentParser(http_resp)
