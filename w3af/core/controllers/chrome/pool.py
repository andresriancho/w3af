"""
pool.py

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
import time

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.chrome.instrumented import InstrumentedChrome


class ChromePool(object):
    """
    An InstrumentedChrome pool with two objectives:

        * Limit the number of InstrumentedChrome instances

        * Reduce the overhead associated with creating new InstrumentedChrome
          instances, which translates to creating new Pool(), ChromeProcess()
          and DebugChromeInterface()

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    # Max number of InstrumentedChrome instances
    MAX_INSTANCES = 20

    # Max number of tasks per instance, after this the instance is killed
    # and a new one is spawned.
    MAX_TASKS = 20

    # The max time to wait for a chrome instance to be available
    GET_FREE_CHROME_RETRY_MAX_TIME = 60

    # Log statistics every N requests
    LOG_STATS_EVERY = 20

    def __init__(self, uri_opener):
        # Store for InstrumentedChrome instances
        self._in_use = set()
        self._free = set()

        # The uri_opener is required to create an InstrumentedChrome instance
        self._uri_opener = uri_opener

        self.log_counter = 0

    def log_stats(self):
        """
        Log stats every N requests for a chrome instance

        :return: None, write output to log file.
        """
        # Log this information only once every N requests
        self.log_counter += 1
        if self.log_counter % self.LOG_STATS_EVERY != 0:
            return

        # General stats
        in_use = len(self._in_use)
        free = len(self._free)

        args = (free, in_use, self.MAX_INSTANCES)
        msg = 'Chrome pool stats (free:%s / in_use:%s / max:%s)'
        om.out.debug(msg % args)

        # Chrome in use time stats
        def sort_by_time(c1, c2):
            return cmp(c1.current_task_start, c2.current_task_start)

        in_use = list(self._in_use)
        in_use.sort(sort_by_time)
        top_offenders = in_use[:5]

        chrome_info = []

        for chrome in top_offenders:
            if chrome.current_task_start is None:
                continue

            args = (chrome.id, time.time() - chrome.current_task_start)
            chrome_info.append('(%s, %.2f sec)' % args)

        chrome_info = ' '.join(chrome_info)
        om.out.debug('Chrome browsers with more in use time: %s' % chrome_info)

    def get(self, http_traffic_queue, timeout=GET_FREE_CHROME_RETRY_MAX_TIME):
        """

        :param http_traffic_queue: The Queue.Queue instance where requests and
                                   responses are written by the Chrome browser

        :param timeout: Timeout to wait for a Chrome instance to be ready

        :return: An InstrumentedChrome instance
        """
        self.log_stats()

        time_waited = 0
        start_time = time.time()

        while time_waited < timeout:
            #
            # First try to re-use the chrome instances we have
            #
            for chrome in self._free.copy():
                try:
                    self._free.remove(chrome)
                except KeyError:
                    # The chrome instance was removed from the set by another thread
                    continue
                else:
                    self._in_use.add(chrome)
                    chrome.current_task_start = time.time()
                    chrome.set_traffic_queue(http_traffic_queue)

                    om.out.debug('Found chrome instance in free set: %s' % chrome)

                    return chrome

            #
            # No free chrome instances were found. Create a new one (if there
            # is enough space in the pool)
            #
            chrome_instances = len(self._free) + len(self._in_use)
            if chrome_instances < self.MAX_INSTANCES:
                chrome = PoolInstrumentedChrome(self._uri_opener,
                                                http_traffic_queue)
                chrome.current_task_start = time.time()

                self._in_use.add(chrome)

                om.out.debug('Created new chrome instance: %s' % chrome)

                return chrome

            #
            # The pool is full, we need to wait for:
            #   * A free chrome instance
            #   * A space in the pool
            #
            # om.out.debug('The chrome pool is full. Waiting...')
            time.sleep(1)
            time_waited = time.time() - start_time

        raise ChromePoolException('Timed out waiting for a chrome instance')

    def free(self, chrome):
        chrome.free_count += 1

        if chrome.free_count > self.MAX_TASKS:
            self.remove(chrome)
            return

        if chrome in self._in_use.copy():
            self._in_use.discard(chrome)
            self._free.add(chrome)
            chrome.current_task_start = None

    def remove(self, chrome):
        self._in_use.discard(chrome)
        self._free.discard(chrome)
        chrome.terminate()

    def terminate(self):
        for chrome in self._free.copy():
            chrome.terminate()

        for chrome in self._in_use.copy():
            chrome.terminate()


class HTTPTrafficQueue(object):
    """
    InstrumentedChrome sends both HTTP request and HTTP response to the queue,
    but we only need the HTTP request.

    This class is a wrapper that removes the HTTP response in put() calls
    to the fuzzable request queue.
    """
    def __init__(self, fuzzable_request_queue):
        self.fuzzable_request_queue = fuzzable_request_queue

    def put(self, (http_request, http_response)):
        return self.fuzzable_request_queue.put(http_request)


class PoolInstrumentedChrome(InstrumentedChrome):
    def __init__(self, uri_opener, http_traffic_queue):
        super(PoolInstrumentedChrome, self).__init__(uri_opener, http_traffic_queue)

        # Stores the time when we release the instance to the user
        self.current_task_start = None

        # The number of times this instance has been free'ed back to the pool
        # This is used by the pool to terminate "old" instances
        self.free_count = 0

    def set_traffic_queue(self, http_traffic_queue):
        # First empty the old queue to release any items we might be referencing
        # This would be done by the gc, but I want to be explicit about it.
        while self.http_traffic_queue.qsize():
            try:
                self.http_traffic_queue.get_nowait()
            except:
                pass

        self.http_traffic_queue = http_traffic_queue


class ChromePoolException(Exception):
    pass
