"""
crawler.py

Copyright 2018 Andres Riancho

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

from w3af.core.controllers.chrome.pool import ChromePool, HTTPTrafficQueue
from w3af.core.data.fuzzer.utils import rand_alnum


class ChromeCrawler(object):
    """
    Use Google Chrome to crawl a site.

    The basic steps are:
        * Get an InstrumentedChrome instance from the chrome pool
        * Load a URL
        * Receive the HTTP requests generated during loading
        * Send the HTTP requests to the caller
    """

    def __init__(self, uri_opener):
        """

        :param uri_opener: The uri opener required by the InstrumentedChrome
                           instances to open URLs via the HTTP proxy daemon.
        """
        self._uri_opener = uri_opener
        self._pool = ChromePool(self._uri_opener)

    def crawl(self, url, fuzzable_request_queue):
        """
        :param url: The URL to crawl
        :param fuzzable_request_queue: Queue.Queue() where HTTP requests are sent

        :return: True if the crawling process completed successfully, otherwise
                 exceptions are raised.
        """
        debugging_id = rand_alnum(8)

        args = (url, debugging_id)
        msg = 'Starting chrome crawler for %s (did: %s)'

        om.out.debug(msg % args)

        http_traffic_queue = HTTPTrafficQueue(fuzzable_request_queue)

        try:
            chrome = self._pool.get(http_traffic_queue=http_traffic_queue)
        except Exception, e:
            args = (e, debugging_id)
            msg = 'Failed to get a chrome instance: "%s" (did: %s)'
            om.out.debug(msg % args)

            raise ChromeCrawlerException('Failed to get a chrome instance: "%s"' % e)

        args = (chrome, url, debugging_id)
        om.out.debug('Using %s to load %s (did: %s)' % args)

        try:
            chrome.load_url(url)
        except Exception, e:
            args = (url, chrome, e, debugging_id)
            msg = 'Failed to load %s using %s: "%s" (did: %s)'
            om.out.debug(msg % args)

            # Since we got an error we remove this chrome instance from the pool
            # it might be in an error state
            self._pool.remove(chrome)

            args = (url, chrome, e)
            raise ChromeCrawlerException('Failed to load %s using %s: "%s"' % args)

        try:
            chrome.wait_for_load()
        except Exception, e:
            args = (url, chrome, e, debugging_id)
            msg = ('Exception raised while waiting for page load of %s '
                   'using %s: "%s" (did: %s)')
            om.out.debug(msg % args)

            # Since we got an error we remove this chrome instance from the pool
            # it might be in an error state
            self._pool.remove(chrome)

            args = (url, chrome, e)
            msg = ('Exception raised while waiting for page load of %s '
                   'using %s: "%s"')
            raise ChromeCrawlerException(msg % args)

        # Success! Return the chrome instance to the pool
        self._pool.free(chrome)

        args = (http_traffic_queue.count, chrome, debugging_id)
        msg = 'Extracted %s new HTTP requests using %s (did: %s)'
        om.out.debug(msg % args)

        return True

    def terminate(self):
        self._pool.terminate()
        self._uri_opener = None


class ChromeCrawlerException(Exception):
    pass
