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
import copy

from stopit import ThreadingTimeout, TimeoutException

from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.controllers.plugins.plugin import Plugin
from w3af.core.controllers.misc.decorators import retry
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404

import w3af.core.controllers.output_manager as om


class CrawlPlugin(Plugin):
    """
    This is the base class for crawl plugins, all crawl plugins should
    inherit from it and implement the following methods:
        1. crawl(...)

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    # in seconds
    PLUGIN_TIMEOUT = 5 * 60

    def __init__(self):
        Plugin.__init__(self)

    def crawl_wrapper(self, fuzzable_request):
        """
        Wrapper around the crawl method in order to perform some generic tasks.
        """
        # I copy the fuzzable request, to avoid cross plugin contamination
        # in other words, if one plugin modified the fuzzable request object
        # INSIDE that plugin, I don't want the next plugin to suffer from that
        fuzzable_request_copy = safe_deepcopy(fuzzable_request)

        # Crawl with timeout
        try:
            with ThreadingTimeout(self.PLUGIN_TIMEOUT, swallow_exc=False):
                return self.crawl(fuzzable_request_copy)
        except TimeoutException:
            msg = '[timeout] The "%s" plugin took more than %s seconds to'\
                  ' complete the crawling of "%s", killing it!'

            om.out.debug(msg % (self.get_name(),
                                self.PLUGIN_TIMEOUT,
                                fuzzable_request.get_url()))

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
    
    def http_get_and_parse(self, url, *args, **kwargs):
        """
        Perform an HTTP GET to url, and if the response is not a 404 then put()
        a FuzzableRequest with the url in the output queue, so it can be
        parsed later by web_spider.py (or any other plugin which does parsing)
        
        :return: The http response that was generated as a response to "GET url"
        """
        fr = FuzzableRequest(url, method='GET')

        http_response = self._uri_opener.send_mutant(fr, cache=True)

        # The 204 check is because of Plugin.handle_url_error()
        if not is_404(http_response) and not http_response.get_code() == 204:
            self.output_queue.put(fr)

            on_success = kwargs.get('on_success', None)
            if on_success is not None:
                on_success(http_response, url, *args)

        return http_response


@retry(2, delay=0.5, backoff=1.1)
def safe_deepcopy(instance):
    """
    In most cases this will just be a wrapper around copy.deepcopy(instance)
    without any added features, but when that fails because of a race condition
    such as dictionary changed size during iteration - crawl_plugin.py #8956 ,
    then we retry.

    I don't want to debug the real issue since it only happen once and I can
    live with the retry.

    :param instance: The object instance we want to copy
    :return: A deep copy of the instance
    """
    return copy.deepcopy(instance)