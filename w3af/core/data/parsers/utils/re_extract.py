"""
re_extract.py

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
import re

from w3af.core.data.parsers.doc.baseparser import BaseParser
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers import URL_RE, RELATIVE_URL_RE


class ReExtract(BaseParser):
    """
    A helper that extracts URLs from a string using regular expressions.

    THIS CODE IS SLOW! USE WITH CARE!

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    # Matches
    # "PHP/5.2.4-2ubuntu5.7", "Apache/2.2.8", "mod_python/3.3.1"
    # used in _find_relative() method
    PHP_VERSION_RE = re.compile('.*?/\d\.\d\.\d')
    QUOTES = {"'", '"'}

    def __init__(self, doc_string, base_url, encoding, relative=True,
                 require_quotes=False):
        self._re_urls = set()

        self._encoding = encoding
        self._base_url = base_url
        self._require_quotes = require_quotes
        self._doc_string = doc_string
        self._relative = relative

    def parse(self):
        """
        Get the URLs using a regex
        """
        self._extract_full_urls(self._doc_string)

        if self._relative:
            self._extract_relative_urls(self._doc_string)

    def _is_quoted(self, url_mo, doc_string):
        start, end = url_mo.span()
        doc_string_len = len(doc_string)

        if end == doc_string_len:
            return False

        if doc_string[start-1] not in self.QUOTES:
            return False

        if doc_string[end] not in self.QUOTES:
            return False

        return True

    def _extract_full_urls(self, doc_string):
        """
        Detect full URLs, which look like http://foo/bar?id=1
        """
        for url_mo in URL_RE.finditer(doc_string):
            if self._require_quotes:
                if not self._is_quoted(url_mo, doc_string):
                    continue

            try:
                url = URL(url_mo.group(0), encoding=self._encoding)
            except ValueError:
                pass
            else:
                self._re_urls.add(url)

    def _extract_relative_urls(self, doc_string):
        """
        Now detect some relative URL's (also using regexs)
        """
        # TODO: Also matches //foo/bar.txt and http://host.tld/foo/bar.txt
        # I'm removing those matches with the filter
        relative_urls = RELATIVE_URL_RE.finditer(doc_string)
        filter_false_urls = self._filter_false_urls

        for url_mo in filter(filter_false_urls, relative_urls):
            if self._require_quotes:
                if not self._is_quoted(url_mo, doc_string):
                    continue

            try:
                url = self._base_url.url_join(url_mo.group(0)).url_string
                url = URL(self._decode_url(url), encoding=self._encoding)
            except ValueError:
                # In some cases, the relative URL is invalid and triggers an
                # ValueError: Invalid URL "%s" exception. All we can do at this
                # point is to ignore this "fake relative URL".
                pass
            else:
                url_lower = url.url_string.lower()

                if url_lower.startswith('http://') or \
                url_lower.startswith('https://'):

                    self._re_urls.add(url)

    def _filter_false_urls(self, potential_url_mo):
        potential_url = potential_url_mo.group(0)

        if potential_url.startswith('//'):
            return False

        if potential_url.startswith('://'):
            return False

        if potential_url.startswith('HTTP/'):
            return False

        if self.PHP_VERSION_RE.match(potential_url):
            return False

        return True

    def get_references(self):
        """
        A list with the URLs extracted using regular expressions.
        """
        return list(self._re_urls)
