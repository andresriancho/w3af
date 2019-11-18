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
import itertools

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.chrome.instrumented.main import InstrumentedChrome
from w3af.core.controllers.core_helpers.consumers.base_consumer import BaseConsumer


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

    #
    # Min number of InstrumentedChrome instances
    #
    # If the number of threads running web_spider (crawl plugin, handled by
    # crawl_infrastructure that inherits from BaseConsumer) is greater than the
    # number of InstrumentedChrome instances then the web_spider calls will
    # start to wait too long and potentially timeout because there is no free
    # InstrumentedChrome
    #
    MIN_INSTANCES = BaseConsumer.THREAD_POOL_SIZE

    # Max number of tasks per instance, after this the instance is killed
    # and a new one is spawned.
    MAX_TASKS = 20

    # The max time to wait for a chrome instance to be available
    GET_FREE_CHROME_RETRY_MAX_TIME = 60

    # Log statistics every N requests
    LOG_STATS_EVERY = 20

    def __init__(self, uri_opener, max_instances=None):
        # Store for InstrumentedChrome instances
        self._in_use = set()
        self._free = set()

        # The uri_opener is required to create an InstrumentedChrome instance
        self._uri_opener = uri_opener

        self.log_counter = 0
        self.max_instances_configured = max_instances or self.MAX_INSTANCES

        min_error_message = ('The number of instances in the ChromePool needs'
                             ' to be greater than %s in order to prevent timeouts'
                             ' and dead-locks in the web_spider plugin. The specified'
                             ' number of instances was %s.')
        min_error_message %= (self.MIN_INSTANCES - 1, self.max_instances_configured)
        assert self.max_instances_configured >= self.MIN_INSTANCES, min_error_message

    def log_stats(self, force=False):
        """
        Log stats every N requests for a chrome instance

        :return: None, write output to log file.
        """
        # Log this information only once every N requests
        self.log_counter += 1
        if (self.log_counter % self.LOG_STATS_EVERY != 0) and not force:
            return

        #
        # Instance use stats
        #
        in_use = len(self._in_use)
        free = len(self._free)

        args = (free, in_use, self.max_instances_configured)
        msg = 'Chrome pool stats (free:%s / in_use:%s / max:%s)'
        om.out.debug(msg % args)

        #
        # Instance memory usage stats
        #
        total_private = 0
        memory_usage = []

        for chrome in itertools.chain(self._in_use.copy(), self._free.copy()):
            try:
                private, shared = chrome.get_memory_usage()
            except Exception, e:
                om.out.debug('Failed to retrieve the chrome instance memory usage: "%s"' % e)
                continue

            if private is None:
                continue

            total_private += private
            memory_usage.append((chrome.id, private))

        if memory_usage:
            om.out.debug('Total chrome memory usage (private memory): %s kb' % total_private)

            def sort_by_usage(a, b):
                return cmp(b[1], a[1])

            memory_usage.sort(sort_by_usage)

            data = ' '.join('(%s, %s)' % (_id, mem) for (_id, mem) in memory_usage)
            om.out.debug('Chrome memory usage details (id, kb): %s' % data)

        #
        # Chrome in use time stats
        #
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

    def get(self,
            http_traffic_queue,
            timeout=GET_FREE_CHROME_RETRY_MAX_TIME,
            debugging_id=None):
        """

        :param http_traffic_queue: The Queue.Queue instance where requests and
                                   responses are written by the Chrome browser

        :param timeout: Timeout to wait for a Chrome instance to be ready

        :param debugging_id: Unique identifier for this call

        :return: An InstrumentedChrome instance
        """
        self.log_stats()

        time_waited = 0
        start_time = time.time()

        while time_waited < timeout:
            #
            # Make sure the number of chrome instances does not exceed the max
            #
            # The problem with the pool is that it doesn't lock on each call
            # to get(), so multiple threads might create a chrome instance at
            # the same time and exceed the max.
            #
            # The problem is fixed by reducing the size of the chrome pool
            # each time it exceeds the max
            #
            chrome_instances = len(self._free) + len(self._in_use)
            if chrome_instances > self.max_instances_configured:
                for chrome in self._free.copy():
                    try:
                        self._free.remove(chrome)
                    except KeyError:
                        # The chrome instance was removed from the set by
                        # another thread
                        continue
                    else:
                        # We just remove one free instance on each call to
                        # get(), this should slowly reduce the number of extra
                        # instances
                        break

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

                    msg = 'Found chrome instance in free set: %s (did: %s)'
                    args = (chrome, debugging_id)
                    om.out.debug(msg % args)

                    msg = 'ChromePool.get() took %.2f seconds to re-use an instance (did: %s)'
                    spent = time.time() - start_time
                    args = (spent, debugging_id)
                    om.out.debug(msg % args)

                    return chrome

            #
            # No free chrome instances were found. Create a new one (if there
            # is enough space in the pool)
            #
            chrome_instances = len(self._free) + len(self._in_use)
            if chrome_instances < self.max_instances_configured:
                om.out.debug('Creating new chrome instance (did: %s)' % debugging_id)

                chrome = PoolInstrumentedChrome(self._uri_opener,
                                                http_traffic_queue)
                chrome.current_task_start = time.time()

                self._in_use.add(chrome)

                args = (chrome, debugging_id)
                om.out.debug('Created new chrome instance: %s (did: %s)' % args)

                spent = time.time() - start_time
                args = (spent, debugging_id)
                msg = 'ChromePool.get() took %.2f seconds to create an instance (did: %s)'
                om.out.debug(msg % args)

                return chrome

            #
            # The pool is full, we need to wait for:
            #   * A free chrome instance
            #   * A space in the pool
            #
            # om.out.debug('The chrome pool is full. Waiting...')
            time.sleep(0.2)
            time_waited = time.time() - start_time

        self.log_stats(force=True)
        raise ChromePoolException('Timed out waiting for a chrome instance')

    def get_free_instances(self):
        return self._free

    def free(self, chrome):
        chrome.free_count += 1

        if chrome.free_count > self.MAX_TASKS:
            self.remove(chrome, 'MAX_TASKS exceeded')
            return

        if chrome in self._in_use.copy():
            msg = ('Chrome instance %s with free_count %s will be marked as'
                   ' free in ChromePool')
            args = (chrome, chrome.free_count)
            om.out.debug(msg % args)

            self._in_use.discard(chrome)
            self._free.add(chrome)
            chrome.current_task_start = None
        else:
            om.out.debug('Chrome pool bug! Called free() on an instance that'
                         ' is not marked as in-use by the pool internals.')

    def remove(self, chrome, reason):
        self._in_use.discard(chrome)
        self._free.discard(chrome)
        chrome.terminate()

        args = (chrome, reason)
        om.out.debug('Removed %s from pool, reason: %s' % args)

    def terminate(self):
        om.out.debug('Calling terminate on all chrome instances')

        while len(self._free) or len(self._in_use):
            for chrome in self._free.copy():
                self.remove(chrome, 'terminate')

            for chrome in self._in_use.copy():
                self.remove(chrome, 'terminate')

        om.out.debug('All chrome instances have been terminated')


class PoolInstrumentedChrome(InstrumentedChrome):
    def __init__(self, uri_opener, http_traffic_queue):
        super(PoolInstrumentedChrome, self).__init__(uri_opener, http_traffic_queue)

        # Stores the time when we release the instance to the user
        self.current_task_start = None

        # The number of times this instance has been free'ed back to the pool
        # This is used by the pool to terminate "old" instances
        self.free_count = 0


class ChromePoolException(Exception):
    pass
