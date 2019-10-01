"""
robots_txt.py

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
import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.kb.info import Info


class robots_txt(CrawlPlugin):
    """
    Analyze the robots.txt file and find new URLs
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    @runonce(exc_class=RunOnce)
    def crawl(self, fuzzable_request, debugging_id):
        """
        Get the robots.txt file and parse it.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                (among other things) the URL to test.
        """
        base_url = fuzzable_request.get_url().base_url()
        robots_url = base_url.url_join('robots.txt')
        http_response = self._uri_opener.GET(robots_url, cache=True)

        if is_404(http_response):
            return

        # Send the robots.txt file to the core, even if we don't find anything
        # in it, it might be interesting to other plugins
        self.worker_pool.map(self.http_get_and_parse, [robots_url])

        urls = self._extract_urls(base_url, http_response)
        if not urls:
            # This is most likely a is_404() false positive, the file might
            # exist but is not a valid robots.txt, or it has all comments,
            # etc.
            return

        # Send the new knowledge to the core!
        self.worker_pool.map(self.http_get_and_parse, urls)

        # Save it to the kb!
        desc = ('A robots.txt file was found at: "%s", this file might'
                ' expose private URLs and requires a manual review. The'
                ' scanner will add all URLs listed in this files to the'
                ' analysis queue.')
        desc %= robots_url

        i = Info('robots.txt file', desc, http_response.id, self.get_name())
        i.set_url(robots_url)

        kb.kb.append(self, 'robots.txt', i)
        om.out.information(i.get_desc())

    def _extract_urls(self, base_url, http_response):
        """
        Extract the entries from the robots.txt response

        :param base_url: URL with the base path
        :param http_response: HTTP response with robots.txt
        :return: URLs found in the robots.txt file
        """
        dirs = []

        for line in http_response.get_body().split('\n'):

            line = line.strip()

            if not len(line):
                continue

            if line[0] == '#':
                continue

            if 'ALLOW' not in line.upper():
                continue

            if ':' not in line.upper():
                continue

            url = line[line.find(':') + 1:]
            url = url.strip()
            try:
                url = base_url.url_join(url)
            except:
                # Simply ignore the invalid URL
                pass
            else:
                dirs.append(url)

        return dirs

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin searches for the robots.txt file, and parses it.

        This file is used to as an ACL that defines what URL's a search engine
        can access. By parsing this file, you can get more information about the
        target web application.
        """
