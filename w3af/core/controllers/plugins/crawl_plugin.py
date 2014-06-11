"""
crawl_plugin.py

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
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.controllers.plugins.plugin import Plugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404


class CrawlPlugin(Plugin):
    """
    This is the base class for crawl plugins, all crawl plugins should
    inherit from it and implement the following methods:
        1. crawl(...)

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        Plugin.__init__(self)

    def crawl_wrapper(self, fuzzable_request):
        """
        Wrapper around the crawl method in order to perform some generic tasks.
        """
        # I copy the fuzzable request, to avoid cross plugin contamination
        # in other words, if one plugin modified the fuzzable request object
        # INSIDE that plugin, I don't want the next plugin to suffer from that
        fuzzable_request_copy = fuzzable_request.copy()
        return self.crawl(fuzzable_request_copy)

    def crawl(self, fuzzable_request):
        """
        This method MUST be implemented on every plugin.

        :param fuzzable_request: Represents an HTTP request, with its URL and
                                 parameters.

        :return: A list with of new fuzzable request objects found by this
                 plugin. Can be empty.
        """
        msg = 'Plugin is not implementing required method crawl'
        raise BaseFrameworkException(msg)

    discover_wrapper = crawl_wrapper

    def get_type(self):
        return 'crawl'
    
    def http_get_and_parse(self, url):
        """
        Perform an HTTP GET to url, and if the response is not a 404 then put()
        a FuzzableRequest with the url in the output queue, so it can be
        parsed later by web_spider.py (or any other plugin which does parsing)
        
        :return: The http response that was generated as a response to "GET url"
        """
        fr = FuzzableRequest(url, method='GET')

        try:
            http_response = self._uri_opener.send_mutant(fr, cache=True)
        except BaseFrameworkException:
            pass
        else:
            if not is_404(http_response):
                self.output_queue.put(fr)
            
            return http_response
