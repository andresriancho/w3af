"""
dom_dump.py

Copyright 2019 Andres Riancho

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

from w3af.core.controllers.chrome.crawler.exceptions import ChromeCrawlerException
from w3af.core.controllers.chrome.devtools.exceptions import (ChromeInterfaceException,
                                                              ChromeInterfaceTimeout)


class ChromeCrawlerDOMDump(object):
    """
    Extract links and forms from the rendered HTML. In some cases the
    rendered DOM / HTML and then HTML received in the HTTP response are
    very different, so we send the rendered DOM to the DocumentParser to
    extract new information
    """

    RENDERED_VS_RAW_RATIO = 0.1

    def __init__(self, pool, debugging_id):
        self._chrome_pool = pool
        self._debugging_id = debugging_id

    def get_name(self):
        return 'DOM dump'

    def _should_parse_dom(self, dom, raw_body):
        """
        Call the DocumentParser (which is an expensive process) only if the
        rendered response shows significant changes. Just measure the size,
        any increase / decrease will make it.

        :return: True if we should parse the DOM
        """
        raw_body_len = len(raw_body)
        rendered_len = len(dom)

        if rendered_len > raw_body_len * (1 + self.RENDERED_VS_RAW_RATIO):
            return True

        if rendered_len < raw_body_len * (1 - self.RENDERED_VS_RAW_RATIO):
            return True

        return False

    def crawl(self,
              chrome,
              url):
        """
        Parses the DOM that is loaded into Chrome using DocumentParser.

        :param chrome: An InstrumentedChrome instance
        :return: None, the new URLs and forms are sent to the chrome instance
                 http_traffic_queue.
        """
        #
        # Get the first HTTP response.
        #
        # Should never be None, but in case it is... we want to find it early
        # on the crawl() method.
        #
        first_http_response = chrome.get_first_response()
        if first_http_response is None:
            #
            # This should never happen, because we reached this code section after
            # crawler/main.py did an initial page load
            #
            msg = 'The %s browser first HTTP response is None (did: %s)'
            args = (chrome, self._debugging_id)
            om.out.debug(msg % args)
            return

        try:
            dom = chrome.get_dom()
        except (ChromeInterfaceException, ChromeInterfaceTimeout) as cie:
            msg = 'Failed to get the DOM from chrome browser %s: "%s" (did: %s)'
            args = (chrome, cie, self._debugging_id)
            om.out.debug(msg % args)

            # Since we got an error we remove this chrome instance from the
            # pool, it might be in an error state
            self._chrome_pool.remove(chrome, 'failed to get DOM')

            raise

        if dom is None:
            msg = 'Chrome returned a null DOM (did: %s)'
            args = (self._debugging_id,)
            om.out.debug(msg % args)

            # Since we got an error we remove this chrome instance from the
            # pool, it might be in an error state
            self._chrome_pool.remove(chrome, 'DOM was None')

            raise ChromeCrawlerException('Failed to get the DOM from chrome browser')

        if not self._should_parse_dom(dom, first_http_response.get_body()):
            msg = 'Decided not to parse the DOM (did: %s)'
            args = (self._debugging_id,)
            om.out.debug(msg % args)
            return

        first_http_request = chrome.get_first_request()

        dom_http_response = first_http_response.copy()
        dom_http_response.set_body(dom)

        # This will call CrawlFilterQueue.put()
        queue_data = (first_http_request,
                      dom_http_response,
                      self._debugging_id)

        http_traffic_queue = chrome.get_traffic_queue()
        http_traffic_queue.put(queue_data)

    def get_debugging_id(self):
        return self._debugging_id
