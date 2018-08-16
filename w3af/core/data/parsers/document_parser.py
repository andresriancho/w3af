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
from w3af.core.data.parsers.doc.html import HTMLParser
from w3af.core.data.parsers.doc.pdf import PDFParser
from w3af.core.data.parsers.doc.swf import SWFParser
from w3af.core.data.parsers.doc.wml_parser import WMLParser
from w3af.core.data.parsers.doc.javascript import JavaScriptParser
from w3af.core.controllers.exceptions import BaseFrameworkException


class DocumentParser(object):
    """
    This class is a document parser.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    # WARNING! The order of this list is important. See note below
    PARSERS = [WMLParser,
               JavaScriptParser,
               PDFParser,
               SWFParser,
               HTMLParser]

    def __init__(self, http_resp):
        """
        Create the proper parser instance, please note that the order in which
        we ask for the type is not random, first we discard the images which
        account for a great % of the URLs in a site, then we ask for WML which
        is a very specific thing to match, then we try JavaScript, PDF and SWF
        (also very specific) and finally we'll try to parse using the HTMLParser
        which will return True to "can_parse" in lots of cases (even when we're
        unsure that the response is really an HTML document).
        """
        self._parser = None
        self._response_repr = None

        if http_resp.is_image():
            msg = 'There is no parser for images.'
            raise BaseFrameworkException(msg)

        for parser in self.PARSERS:
            if parser.can_parse(http_resp):
                self._parser = parser(http_resp)
                self._parser.parse()
                self._response_repr = repr(http_resp)
                break

        if self._parser is None:
            msg = 'There is no parser for "%s".' % http_resp.get_url()
            raise BaseFrameworkException(msg)

    @staticmethod
    def can_parse(http_resp):
        if http_resp.is_image():
            return False

        for parser in DocumentParser.PARSERS:
            if parser.can_parse(http_resp):
                return True

        return False

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

        The URL lists are ordered alphabetically, this small improvement tries
        to improve issues with different w3af scans finding different number of
        URLs. The root cause for the issue is w3af's threaded architecture
        which makes everything run in an unpredictable order. Ordering the
        output alphabetically tries to impose an order in which things should
        be processed.

        Returned in two separate lists because the first ones
        are much more accurate and they might deserve a different
        treatment.
        """
        parsed_refs, re_refs = self._parser.get_references()

        parsed_refs.sort(sort_by_url)
        re_refs.sort(sort_by_url)

        return parsed_refs, re_refs

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
                       "*@domain". If domain is None then all email addresses
                       are returned.
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

    def get_tags_by_filter(self, tags, yield_text=False):
        """
        :param tags: The tag filter
        :return: Yield tags which match the filter
        """
        for i in self._parser.get_tags_by_filter(tags, yield_text=yield_text):
            yield i

    def get_clear_text_body(self):
        """
        :return: Only the text, no tags, which is present in a document.
        """
        return self._parser.get_clear_text_body()

    def clear(self):
        return self._parser.clear()

    def get_parser(self):
        return self._parser

    def __repr__(self):
        if self._parser:
            klass = self._parser.__class__.__name__
        else:
            klass = None

        return '<%s DocumentParser for "%s">' % (klass, self._response_repr)

    __str__ = __repr__


def document_parser_factory(http_resp):
    return DocumentParser(http_resp)


def sort_by_url(url_a, url_b):
    return cmp(url_a.url_string, url_b.url_string)
