"""
wsdl_finder.py

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

from w3af.core.data.parsers.doc.url import URL
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter


class wsdl_finder(CrawlPlugin):
    """
    Find web service definitions files.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    WSDL = ('?wsdl',
            '?WSDL')

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._already_tested = ScalableBloomFilter()

    def crawl(self, fuzzable_request, debugging_id):
        """
        If url not in _tested, append a ?WSDL and check the response.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                 (among other things) the URL to test.
        """
        url = fuzzable_request.get_url().uri2url()
        url_string = url.url_string

        if url_string in self._already_tested:
            return

        self._already_tested.add(url_string)

        wsdl_url_generator = self.wsdl_url_generator(url_string)

        self.worker_pool.map(self._do_request, wsdl_url_generator, chunksize=1)

    def wsdl_url_generator(self, url_string):
        for wsdl_parameter in self.WSDL:
            url_to_request = url_string + wsdl_parameter
            url_instance = URL(url_to_request)
            yield url_instance

    def _do_request(self, url_to_request):
        """
        Perform an HTTP request to the url_to_request parameter.
        :return: None.
        """
        try:
            self._uri_opener.GET(url_to_request, cache=True)
        except BaseFrameworkException:
            om.out.debug('Failed to request the WSDL file: ' + url_to_request)
        else:
            # The response is analyzed by the wsdlGreper plugin
            pass

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before the
        current one.
        """
        return ['grep.wsdl_greper']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds new web service descriptions and other web service
        related files by appending "?WSDL" to all URL's and checking the response.
        """
