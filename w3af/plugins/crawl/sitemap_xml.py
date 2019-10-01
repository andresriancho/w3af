"""
sitemap_xml.py

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
import xml.dom.minidom

import w3af.core.controllers.output_manager as om
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class sitemap_xml(CrawlPlugin):
    """
    Analyze the sitemap.xml file and find new URLs

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    @runonce(exc_class=RunOnce)
    def crawl(self, fuzzable_request, debugging_id):
        """
        Get the sitemap.xml file and parse it.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                   (among other things) the URL to test.
        """
        base_url = fuzzable_request.get_url().base_url()
        sitemap_url = base_url.url_join('sitemap.xml')
        response = self._uri_opener.GET(sitemap_url, cache=True)

        if '</urlset>' not in response:
            return

        if is_404(response):
            return

        # Send response to core
        fr = FuzzableRequest.from_http_response(response)
        self.output_queue.put(fr)

        om.out.debug('Parsing xml file with xml.dom.minidom.')
        try:
            dom = xml.dom.minidom.parseString(response.get_body())
        except Exception, e:
            msg = 'Exception while parsing sitemap.xml from %s: "%s"'
            args = (response.get_url(), e)
            om.out.debug(msg % args)
            return

        parsed_url_list = []
        raw_url_list = dom.getElementsByTagName("loc")

        for url in raw_url_list:
            try:
                url = url.childNodes[0].data
            except Exception, e:
                msg = 'Sitemap file at %s has an invalid format: %s'
                args = (response.get_url(), e)
                om.out.debug(msg % args)
                continue

            try:
                url = URL(url)
            except ValueError, ve:
                msg = 'Sitemap file at %s has an invalid URL: "%s"'
                args = (response.get_url(), ve)
                om.out.debug(msg % args)
                continue
            else:
                parsed_url_list.append(url)

        self.worker_pool.map(self.http_get_and_parse, parsed_url_list)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin searches for the sitemap.xml file, and parses it.

        The sitemap.xml file is used by the site administrator to give the
        Google crawler more information about the site. By parsing this file,
        the plugin finds new URLs and other useful information.
        """
