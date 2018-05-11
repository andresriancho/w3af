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
import time

import w3af.core.data.kb.config as cf
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.profiling.took_helper import TookLine
from w3af.core.controllers.core_helpers.consumers.base_consumer import BaseConsumer
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.db.history import HistoryItem
from w3af.core.data.dc.headers import Headers
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class grep(BaseConsumer):
    """
    Consumer thread that takes requests and responses from the queue and
    analyzes them using the user-enabled grep plugins.
    """

    TARGET_DOMAINS = None

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
        max_in_queue_size = 20

        # thread_pool_size defines how many threads we'll use to run grep plugins
        thread_pool_size = 2

        # max_pool_queued_tasks defines how many tasks we'll keep in memory waiting
        # for a worker from the pool to be available
        max_pool_queued_tasks = thread_pool_size * 3

        super(grep, self).__init__(grep_plugins,
                                   w3af_core,
                                   create_pool=False,
                                   #max_pool_queued_tasks=max_pool_queued_tasks,
                                   #thread_pool_size=thread_pool_size,
                                   thread_name='Grep',
                                   max_in_queue_size=max_in_queue_size)
        self._already_analyzed = ScalableBloomFilter()

    def _teardown(self):
        """
        Handle POISON_PILL
        """
        msg = 'Starting Grep consumer _teardown() with %s plugins.'
        om.out.debug(msg % len(self._consumer_plugins))

        for plugin in self._consumer_plugins:
            om.out.debug('Calling %s.end().' % plugin.get_name())
            start_time = time.time()

            try:
                plugin.end()
            except Exception, e:
                msg = 'An exception was found while running %s.end(): "%s"'
                args = (plugin.get_name(), e)
                om.out.error(msg % args)
                continue

            spent_time = time.time() - start_time
            msg = 'Spent %.2f seconds running %s.end().'
            args = (spent_time, plugin.get_name())
            om.out.debug(msg % args)

        om.out.debug('Finished Grep consumer _teardown().')

    def _get_request_response_from_work_unit(self, work_unit):
        """
        In some cases the work unit is a tuple with request / response instances.

        In other cases it is an ID, which needs to be queried from the History DB
        to get the request / response.

        :param work_unit: One of the options explained above
        :return: A request / response tuple
        """
        if not isinstance(work_unit, int):
            request, response = work_unit
        else:
            # Before we sent requests and responses as work units,
            # but since we changed from Queue to CachedQueue for BaseConsumer
            # the database was growing really big (1GB) for storing that traffic
            # and I decided to migrate to using just the response.id and querying
            # the SQLite one extra time.
            history = HistoryItem()
            request, response = history.load_from_file(work_unit)

        # Create a fuzzable request based on the urllib2 request object
        headers_inst = Headers(request.header_items())
        request = FuzzableRequest.from_parts(request.url_object,
                                             request.get_method(),
                                             request.get_data() or '',
                                             headers_inst)

        return request, response

    def _consume(self, work_unit):
        """
        Handle a request/response that needs to be analyzed
        :param work_unit: Request and response in a tuple
        :return: None
        """
        request, response = self._get_request_response_from_work_unit(work_unit)

        # We run this again here to prevent a request / response from being
        # processed twice
        should_grep = self._already_analyzed.add(response.get_uri())
        if not should_grep:
            return

        self._run_observers(request, response)

        # Note that I'm NOT processing the grep plugin data in different
        # threads. This is because it makes no sense (these are all CPU
        # bound).
        for plugin in self._consumer_plugins:

            # Note that if we don't limit the input queue size for the thread
            # pool we might end up with a lot of queued calls here! The calls
            # contain an HTTP response body, so they really use a lot of
            # memory!
            #
            # This is controlled by max_pool_queued_tasks
            self._inner_consume(1, plugin, request, response)
            #self._threadpool.apply_async(self._inner_consume,
            #                             (plugin, request, response))

    def _inner_consume(self, function_id, plugin, request, response):
        """
        Run one plugin against a request/response.

        :param function_id: The function ID added by @task_decorator
        :param plugin: The grep plugin to run
        :param request: The HTTP request
        :param response: The HTTP response
        :return: None, results are saved to KB
        """
        took_line = TookLine(self._w3af_core,
                             plugin.get_name(),
                             'grep',
                             debugging_id=None,
                             method_params={'uri': request.get_uri()})

        try:
            plugin.grep_wrapper(request, response)
        except Exception, e:
            self.handle_exception('grep', plugin.get_name(), request, e)
        else:
            took_line.send()

    def _run_observers(self, request, response):
        """
        Run the observers handling any exception that they might raise
        :return: None
        """
        try:
            for observer in self._observers:
                observer.grep(self, request, response)
        except Exception, e:
            self.handle_exception('grep',
                                  'grep._run_observers()',
                                  'grep._run_observers()', e)

    def should_grep(self, request, response):
        """
        :return: True if I should grep this request/response pair. This method
                 replaces some of the logic that before was in grep_plugin.py,
                 but because of the requirement of a central location to store
                 a bloom filter was moved here.
        """
        if not self._consumer_plugins:
            return False

        # This cache is here to avoid a query to the cf each time a request
        # goes to a grep plugin. Given that in the future the cf will be a
        # sqlite database, this is an important improvement.
        if self.TARGET_DOMAINS is None:
            self.TARGET_DOMAINS = cf.cf.get('target_domains')

        if response.get_url().get_domain() not in self.TARGET_DOMAINS:
            return False

        return True

    def grep(self, request, response):
        """
        Make sure that we only add items to the queue that will be later grep'd
        and then decide how we're going to serialize the request and response
        to be more performant.

        :see: _get_request_response_from_work_unit()
        :param request: HTTP request to grep
        :param response: HTTP response to grep
        :return: None
        """
        if not self.should_grep(request, response):
            return

        if self.in_queue.next_item_saved_to_memory():
            #
            # Just send the request / response, most likely they are going
            # to live in the CachedQueue for only a couple of seconds
            #
            work = (request, response)
        else:
            #
            # Well, this will be a little bit more complicated. We don't
            # want to fill the disk with the data we save in the queue
            # so we just send the ID
            #
            work = response.id

        # Send to the parent class so the data gets saved
        return super(grep, self).in_queue_put(work)
