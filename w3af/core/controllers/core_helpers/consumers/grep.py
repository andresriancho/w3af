"""
grep.py

Copyright 2012 Andres Riancho

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
import sys
import time
import threading

# pylint: disable=E0401
from darts.lib.utils.lru import SynchronizedLRUDict
# pylint: enable=E0401

import w3af.core.data.kb.config as cf
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.profiling.took_helper import TookLine
from w3af.core.controllers.core_helpers.consumers.base_consumer import BaseConsumer
from w3af.core.controllers.core_helpers.status import CoreStatus
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.db.history import HistoryItem
from w3af.core.data.dc.headers import Headers
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.misc.response_cache_key import ResponseCacheKeyCache
from w3af.core.data.misc.encoding import smart_str_ignore


class grep(BaseConsumer):
    """
    Consumer thread that takes requests and responses from the queue and
    analyzes them using the user-enabled grep plugins.
    """

    LOG_QUEUE_SIZES_EVERY = 25
    REPORT_GREP_STATS_EVERY = 25

    EXCLUDE_HEADERS_FOR_HASH = tuple(['date',
                                      'expires',
                                      'last-modified',
                                      'etag',
                                      'x-request-id',
                                      'x-content-duration',
                                      'x-execution-time',
                                      'x-requestid',
                                      'content-length',
                                      'cf-ray',
                                      'set-cookie'])

    def __init__(self, grep_plugins, w3af_core):
        """
        :param grep_plugins: Instances of grep plugins in a list
        :param w3af_core: The w3af core that we'll use for status reporting
        """
        # max_in_queue_size, is the number of items that will be stored in-memory
        # in the consumer queue
        #
        # Any items exceeding max_in_queue_size will be stored on-disk, which
        # is slow but will prevent any high memory usage imposed by this part
        # of the framework
        max_in_queue_size = 25

        # thread_pool_size defines how many threads we'll use to run grep plugins
        thread_pool_size = 10

        # max_pool_queued_tasks defines how many tasks we'll keep in memory waiting
        # for a worker from the pool to be available
        max_pool_queued_tasks = thread_pool_size * 3

        super(grep, self).__init__(grep_plugins,
                                   w3af_core,
                                   create_pool=True,
                                   max_pool_queued_tasks=max_pool_queued_tasks,
                                   thread_pool_size=thread_pool_size,
                                   thread_name=self.get_name(),
                                   max_in_queue_size=max_in_queue_size)

        self._already_analyzed_body = ScalableBloomFilter()
        self._already_analyzed_url = ScalableBloomFilter()

        self._target_domains = None
        self._log_queue_sizes_calls = 0

        self._consumer_plugin_dict = dict((plugin.get_name(), plugin) for plugin in self._consumer_plugins)
        self._first_plugin_name = self._consumer_plugin_dict.keys()[0]

        self._request_response_lru = SynchronizedLRUDict(thread_pool_size * 3)
        self._request_response_processes = dict()
        self._response_cache_key_cache = ResponseCacheKeyCache()

        self._should_grep_stats = {
            'accept': 0,
            'reject-seen-body': 0,
            'reject-seen-url': 0,
            'reject-out-of-scope': 0,
        }

    def get_name(self):
        return 'Grep'

    def _teardown(self):
        """
        Handle POISON_PILL
        """
        msg = 'Starting Grep consumer _teardown() with %s plugins'
        om.out.debug(msg % len(self._consumer_plugins))

        for plugin in self._consumer_plugins:
            om.out.debug('Calling %s.end()' % plugin.get_name())
            start_time = time.time()

            try:
                plugin.end()
            except Exception as exception:
                msg = 'An exception was found while running %s.end(): "%s"'
                args = (plugin.get_name(), exception)
                om.out.debug(msg % args)

                status = FakeStatus(self._w3af_core)
                status.set_current_fuzzable_request('grep', 'n/a')
                status.set_running_plugin('grep',
                                          plugin.get_name(),
                                          log=True)

                exec_info = sys.exc_info()
                enabled_plugins = 'n/a'
                self._w3af_core.exception_handler.handle(status,
                                                         exception,
                                                         exec_info,
                                                         enabled_plugins)
                continue

            spent_time = time.time() - start_time
            msg = 'Spent %.2f seconds running %s.end()'
            args = (spent_time, plugin.get_name())
            om.out.debug(msg % args)

        self._consumer_plugins = dict()
        self._consumer_plugin_dict = dict()
        self._response_cache_key_cache.clear_cache()

        om.out.debug('Finished Grep consumer _teardown()')

    def _get_request_response_from_id_impl(self, http_response_id):
        """
        Just reads the request and response from the files. No threading,
        events, caching, etc.

        :param http_response_id: The HTTP response ID
        :return: An HTTP request and response tuple
        """
        history = HistoryItem()
        request, response = history.load_from_file(http_response_id)

        # Create a fuzzable request based on the urllib2 request object
        headers_inst = Headers(request.header_items())
        request = FuzzableRequest.from_parts(request.url_object,
                                             request.get_method(),
                                             request.get_data() or '',
                                             headers_inst)

        return request, response

    def _get_request_response_from_id(self, http_response_id):
        """
        This is a rather complex method that reads the HTTP request and response
        from disk and makes sure that:

            * Requests and responses are cached in a LRU to prevent reading
              the same data from disk twice in a short period of time

            * Thread events are used to prevent two threads from starting
              to read the same HTTP response ID at the same time, which
              would waste CPU cycles and disk IO.

        :param http_response_id: The HTTP response ID
        :return: A request / response tuple
        """
        #
        # First check if the request and response was already deserialized
        # by another thread and stored in the LRU
        #
        request_response = self._request_response_lru.get(http_response_id, None)
        if request_response is not None:
            request, response = request_response
            return request, response

        #
        # Another thread might have started with the deserialization, check
        # and wait for that thread to finish
        #
        event = self._request_response_processes.get(http_response_id, None)
        if event is not None:
            # Wait for the other thread to finish reading the request and
            # response from disk. Timeout after 20 seconds as a safety measure
            wait_result = event.wait(timeout=20)
            if not wait_result:
                om.out.error('There was a timeout waiting for the'
                             ' deserialization of HTTP request and response'
                             ' with id %s' % http_response_id)
                return None, None

            # Read the data from the LRU. There is a 99,9999% chance it is there
            # since the other thread saved it before setting the event
            request_response = self._request_response_lru.get(http_response_id, None)
            if request_response is not None:
                request, response = request_response
                return request, response

            # There is a 0,0001% chance we get here when the items in the LRU
            # are removed right after being added, if this happens we just
            # continue with the algorithm and read the request / response
            # from the files

        #
        # There are no threads deserializing this HTTP response id, start
        # the process and create an event for others to know they need to
        # wait
        #
        event = threading.Event()
        self._request_response_processes[http_response_id] = event

        try:
            request, response = self._get_request_response_from_id_impl(http_response_id)
            self._request_response_lru[http_response_id] = (request, response)
        finally:
            event.set()
            self._request_response_processes.pop(http_response_id, None)

        return request, response

    def _consume(self, http_response_id):
        """
        Handle a request/response that needs to be analyzed
        :param http_response_id: The HTTP response ID
        :return: None
        """
        self._run_all_plugins(http_response_id)

    def _log_queue_sizes(self):
        """
        The grep consumer will loop really fast through all tasks, if the
        queue sizes are written on every loop, we'll end up with a log file
        full of those lines (with ~10 lines per second with almost the same
        information).

        Call the parent's _log_queue_sizes once every 25 calls to this method.

        :return: None
        """
        self._log_queue_sizes_calls += 1

        if (self._log_queue_sizes_calls % self.LOG_QUEUE_SIZES_EVERY) != 0:
            return

        return super(grep, self)._log_queue_sizes()

    def _run_all_plugins(self, http_response_id):
        """
        Run one plugin against a request/response.

        :param http_response_id: HTTP response ID
        :return: None, results are saved to KB
        """
        for plugin_name in self._consumer_plugin_dict:
            # Note that if we don't limit the input queue size for the thread
            # pool we might end up with a lot of queued calls here! The calls
            # contain an HTTP response body, so they really use a lot of
            # memory!
            #
            # This is controlled by max_pool_queued_tasks
            args = (plugin_name, http_response_id)
            self._threadpool.apply_async(self._run_one_plugin, args)

    def _get_plugin_from_name(self, plugin_name):
        plugin = self._consumer_plugin_dict.get(plugin_name, None)

        if plugin is None:
            msg = ('Internal error in grep consumer: plugin with name %s'
                   ' does not exist in dict.')
            args = (plugin_name,)
            om.out.error(msg % args)

        return plugin

    def _run_one_plugin(self, plugin_name, http_response_id):
        """
        :param plugin_name: Grep plugin name to run
        :param http_response_id: HTTP response ID
        :return: None
        """
        plugin = self._get_plugin_from_name(plugin_name)
        if plugin is None:
            return

        request, response = self._get_request_response_from_id(http_response_id)
        if request is None:
            return

        self._run_observers(plugin_name, request, response)

        took_line = TookLine(self._w3af_core,
                             plugin_name,
                             'grep',
                             debugging_id=None,
                             method_params={'uri': request.get_uri()})

        try:
            plugin.grep_wrapper(request, response)
        except Exception, e:
            self.handle_exception('grep', plugin_name, request, e)
        else:
            took_line.send()

    def _run_observers(self, plugin_name, request, response):
        """
        Run the observers handling any exception that they might raise
        :return: None
        """
        # In the current version this method is run for every call to
        # a grep plugin: if 20 grep plugins are enabled, then this method
        # is called 20 times for each request and response pair
        #
        # This is unnecessary, to reduce the number of calls to the observers
        # we check that the plugin_name is the first one (just picked an
        # arbitrary one) from the consumer list
        if plugin_name != self._first_plugin_name:
            return

        for observer in self._observers:
            try:
                observer.grep(self, request, response)
            except Exception, e:
                self.handle_exception('grep',
                                      'grep._run_observers()',
                                      'grep._run_observers()',
                                      e)

    def should_grep(self, request, response):
        """
        :return: True if I should grep this request/response pair. This method
                 replaces some of the logic that before was in grep_plugin.py,
                 but because of the requirement of a central location to store
                 a bloom filter was moved here.
        """
        if not self._consumer_plugins:
            return False

        self._print_should_grep_stats()

        # This cache is here to avoid a query to the cf each time a request
        # goes to a grep plugin. Given that in the future the cf will be a
        # sqlite database, this is an important improvement.
        if self._target_domains is None:
            self._target_domains = cf.cf.get('target_domains')

        if response.get_url().get_domain() not in self._target_domains:
            self._should_grep_stats['reject-out-of-scope'] += 1
            return False

        #
        # This prevents responses for the same URL from being analyze twice
        #
        # Sometimes the HTTP responses vary in one byte, which will completely
        # break the filter we have implemented below (it uses a hash for
        # the response headers and xml-bones body).
        #
        # This filter is less effective, mainly during the audit phase where the
        # plugins are heavily changing the query-string, but will prevent some HTTP
        # requests and responses from making it to the grep plugins
        #
        if not self._already_analyzed_url.add(response.get_uri()):
            self._should_grep_stats['reject-seen-url'] += 1
            return False

        #
        # This prevents the same HTTP response from being analyze twice
        #
        # The great majority of grep plugins analyze HTTP response bodies,
        # some analyze HTTP response headers, and a very small subset analyzes
        # HTTP requests. Based on these facts it was possible to add these
        # lines to prevent the same HTTP response from being analyzed twice.
        #
        # One of the options I had was to use get_response_cache_key() below,
        # to prevent double processing of HTTP response bodies, but that
        # strategy had more chances of "hiding" some HTTP responses from grep
        # plugins:
        #
        #   * HTTP response A contains header set X and body Y. It will be
        #     processed because it is the first time body Y is seen.
        #
        #   * HTTP response A contains header set Z and body Y. It will be
        #     ignored because Y was already seen.
        #
        # So I decided to use both the headers and body. The filter might be
        # degraded on sites that use HTTP response headers that contain dates
        # or some other value that changes a lot, this issue was reduced by
        # using EXCLUDE_HEADERS_FOR_HASH
        #
        headers = response.dump_headers(exclude_headers=self.EXCLUDE_HEADERS_FOR_HASH)
        headers = smart_str_ignore(headers)

        #
        # Note that using cached_get_response_cache_key() here gives a performance
        # boost, this cache uses the HTTP response body and headers (at least some)
        # as a key. In initial tests using this cache strategy made the
        # `test_should_grep_speed` unittest go from 26 to 9 seconds.
        #
        response_hash = self._response_cache_key_cache.get_response_cache_key(response,
                                                                              headers=headers)

        if not self._already_analyzed_body.add(response_hash):
            self._should_grep_stats['reject-seen-body'] += 1
            return False

        self._should_grep_stats['accept'] += 1
        return True

    def _print_should_grep_stats(self):
        total = 0

        for key in self._should_grep_stats:
            total += self._should_grep_stats[key]

        if (total % self.REPORT_GREP_STATS_EVERY) != 0:
            return

        msg = 'Grep consumer should_grep() stats: %r'
        args = (self._should_grep_stats,)
        om.out.debug(msg % args)

    def grep(self, request, response):
        """
        Make sure that we only add items to the queue that will be later grep'd
        and then decide how we're going to serialize the request and response
        to be more performant.

        This method MUST be fast, it is part of the request-response cycle.
        Any performance issue in this method will delay the whole scan
        engine.

        :see: _get_request_response_from_work_unit()
        :param request: HTTP request to grep
        :param response: HTTP response to grep
        :return: None
        """
        if not self.should_grep(request, response):
            return

        # Send to the parent class so the data gets saved
        return super(grep, self).in_queue_put(response.id)


class FakeStatus(CoreStatus):
    pass
