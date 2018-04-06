"""
javascript.py

Copyright 2014 Andres Riancho

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
from w3af.core.data.parsers.doc.baseparser import BaseParser
from w3af.core.data.parsers.utils.re_extract import ReExtract


class JavaScriptParser(BaseParser):
    """
    This class extracts links from javascript http responses

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    PARSE_TYPES = ('javascript',
                   'ecmascript',
                   'jscript')

    def __init__(self, http_response):
        super(JavaScriptParser, self).__init__(http_response)

        self._re_urls = set()

    @staticmethod
    def can_parse(http_resp):
        """
        :param http_resp: A http response object that contains a document of
                          type HTML / PDF / WML / etc.

        :return: True if the document parameter is a string that contains JS
        """
        response_content_type = http_resp.content_type.lower()

        for _type in JavaScriptParser.PARSE_TYPES:
            if _type in response_content_type:
                return True

        return False

    def parse(self):
        """
        Get the URLs using a regex
        """
        re_extract = ReExtract(self.get_http_response().get_body(),
                               self._base_url, self._encoding,
                               require_quotes=True)
        re_extract.parse()
        self._re_urls = re_extract.get_references()

    def get_references(self):
        """
        Searches for references on a page. w3af searches references in every
        html tag, including:
            - a
            - forms
            - images
            - frames
            - etc.

        :return: Two lists, one with the parsed URLs, and one with the URLs
                 that came out of a regular expression. The second list if less
                 trustworthy.
        """
        return [], list(self._re_urls)

    def get_clear_text_body(self):
        """
        :return: Since this "is already clear text", we'll return the whole body
        """
        return self.get_http_response().body

    get_references_of_tag = get_forms = BaseParser._return_empty_list
    get_comments = BaseParser._return_empty_list
    get_meta_redir = get_meta_tags = get_emails = BaseParser._return_empty_list

