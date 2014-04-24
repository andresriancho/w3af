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

from w3af.core.data.parsers.baseparser import BaseParser
from w3af.core.data.parsers.url import URL
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

    def __init__(self, doc_string, base_url, encoding, relative=True):
        self._re_urls = set()

        self._encoding = encoding
        self._base_url = base_url

        self._parse(doc_string, relative)

    def _parse(self, doc_string, relative):
        """
        Get the URLs using a regex
        """
        self._extract_full_urls(doc_string)

        if relative:
            self._extract_relative_urls(doc_string)

    def _extract_full_urls(self, doc_string):
        """
        Detect full URLs, which look like http://foo/bar?id=1
        """
        for x in URL_RE.findall(doc_string):
            try:
                self._re_urls.add(URL(x[0]))
            except ValueError:
                pass

    def _extract_relative_urls(self, doc_string):
        """
        Now detect some relative URL's (also using regexs)
        """
        # TODO: Also matches //foo/bar.txt and http://host.tld/foo/bar.txt
        # I'm removing those matches with the filter
        relative_urls = RELATIVE_URL_RE.findall(doc_string)
        filter_false_urls = self._filter_false_urls

        for match_tuple in filter(filter_false_urls, relative_urls):
            match_str = match_tuple[0]

            try:
                url = self._base_url.url_join(match_str).url_string
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

    def _filter_false_urls(self, potential_url):
        potential_url = potential_url[0]

        if potential_url.startswith('//') or \
        potential_url.startswith('://') or \
        potential_url.startswith('HTTP/') or \
        self.PHP_VERSION_RE.match(potential_url):
            return False

        return True

    def get_references(self):
        """
        A list with the URLs extracted using regular expressions.
        """
        return list(self._re_urls)
