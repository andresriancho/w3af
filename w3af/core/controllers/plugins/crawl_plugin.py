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
from w3af.core.controllers.misc.safe_deepcopy import safe_deepcopy
from w3af.core.controllers.plugins.plugin import Plugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.exceptions import (BaseFrameworkException,
                                              FourOhFourDetectionException)

import w3af.core.controllers.output_manager as om


class CrawlPlugin(Plugin):
    """
    This is the base class for crawl plugins, all crawl plugins should
    inherit from it and implement the following methods:
        1. crawl(...)

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def discover_wrapper(self, fuzzable_request, debugging_id):
        """
        Wrapper around the crawl method in order to perform some generic tasks.

        :param fuzzable_request: The target to use for infrastructure plugins.
        :param debugging_id: A unique identifier for this call to discover()
        """
        om.out.debug('[%s] Crawling "%s"' % (self.get_name(),
                                             fuzzable_request.get_uri()))

        # I copy the fuzzable request, to avoid cross plugin contamination
        # in other words, if one plugin modified the fuzzable request object
        # INSIDE that plugin, I don't want the next plugin to suffer from that
        fuzzable_request_copy = safe_deepcopy(fuzzable_request)

        try:
            return self.crawl(fuzzable_request_copy, debugging_id)
        except FourOhFourDetectionException, ffde:
            # We simply ignore any exceptions we find during the 404 detection
            # process. FYI: This doesn't break the xurllib error handling which
            # happens at lower layers.
            #
            # https://github.com/andresriancho/w3af/issues/8949
            om.out.debug('%s' % ffde)

    def crawl(self, fuzzable_request, debugging_id):
        """
        This method MUST be implemented on every plugin.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: Represents an HTTP request, with its URL and
                                 parameters.

        :return: A list with of new fuzzable request objects found by this
                 plugin. Can be empty.
        """
        msg = 'Plugin is not implementing required method crawl'
        raise BaseFrameworkException(msg)

    def get_type(self):
        return 'crawl'
    
    def http_get_and_parse(self, url, *args, **kwargs):
        """
        Perform an HTTP GET to url, and if the response is not a 404 then put()
        a FuzzableRequest with the url in the output queue, so it can be
        parsed later by web_spider.py (or any other plugin which does parsing)
        
        :return: The http response that was generated as a response to "GET url"
        """
        fr = FuzzableRequest(url, method='GET')

        on_success = kwargs.pop('on_success', None)
        http_response = self._uri_opener.send_mutant(fr, cache=True, *args, **kwargs)

        # The 204 check is because of Plugin.handle_url_error()
        if not is_404(http_response) and not http_response.get_code() == 204:
            self.output_queue.put(fr)

            if on_success is not None:
                on_success(http_response, url, *args)

        return http_response

    def http_get(self, url, *args, **kwargs):
        """
        Similar to `http_get_and_parse` but will not send the HTTP response to
        the core.

        :param url: The URL instance to send the GET request to
        :param args: args for send_mutant
        :param kwargs: kwargs for send_mutant
        :return: The HTTP response
        """
        fr = FuzzableRequest(url, method='GET')

        on_success = kwargs.pop('on_success', None)
        http_response = self._uri_opener.send_mutant(fr, cache=True, *args, **kwargs)

        if on_success is not None:
            on_success(http_response, url, *args)

        return http_response
