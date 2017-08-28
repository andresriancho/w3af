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

from w3af.core.controllers.core_helpers.consumers.constants import POISON_PILL
from w3af.core.controllers.core_helpers.consumers.base_consumer import BaseConsumer
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter


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
        # We use BaseConsumer.THREAD_POOL_SIZE as an arbitrary "low" number
        # to calculate the max_in_queue_size, the basic thinking behind this
        # is that we don't want hundreds of HTTP request + responses queued
        # in memory waiting for the grep plugins to analyze them.
        #
        # If this limit works it means that: If the grep plugins are slow, then
        # the whole scanner will be slow but no excessive memory usage will be
        # found
        max_in_queue_size = BaseConsumer.THREAD_POOL_SIZE * 2

        super(grep, self).__init__(grep_plugins,
                                   w3af_core,
                                   create_pool=False,
                                   thread_name='Grep',
                                   max_in_queue_size=max_in_queue_size)
        self._already_analyzed = ScalableBloomFilter()

    def run(self):
        """
        Consume the queue items
        """
        while True:

            try:
                work_unit = self.in_queue.get()
            except KeyboardInterrupt:
                # https://github.com/andresriancho/w3af/issues/9587
                #
                # If we don't do this, the thread will die and will never
                # process the POISON_PILL, which will end up in an endless
                # wait for .join()
                continue

            if work_unit == POISON_PILL:
                try:
                    self._teardown()
                finally:
                    self.in_queue.task_done()
                    break

            else:
                try:
                    self._consume(work_unit)
                finally:
                    self.in_queue.task_done()

    def _teardown(self):
        """
        Handle POISON_PILL
        """
        for plugin in self._consumer_plugins:
            plugin.end()

    def _consume(self, work_unit):
        """
        Handle a request/response that needs to be analyzed
        :param work_unit: Request and response in a tuple
        :return: None
        """
        request, response = work_unit

        if not self.should_grep(request, response):
            return

        self._run_observers(request, response)

        # Note that I'm NOT processing the grep plugin data in different
        # threads. This is because it makes no sense (these are all CPU
        # bound).
        for plugin in self._consumer_plugins:
            args = (plugin.get_name(), request.get_uri())
            om.out.debug('%s.grep(%s)' % args)

            start_time = time.time()

            try:
                plugin.grep_wrapper(request, response)
            except Exception, e:
                self.handle_exception('grep', plugin.get_name(), request, e)

            spent_time = time.time() - start_time
            args = (plugin.get_name(), request.get_uri(), spent_time)
            om.out.debug('%s.grep(%s) took %.2f seconds to run' % args)

    def _run_observers(self, request, response):
        """
        Run the observers handling any exception that they might raise
        :return: None
        """
        try:
            for observer in self._observers:
                observer.grep(request, response)
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
        # This cache is here to avoid a query to the cf each time a request
        # goes to a grep plugin. Given that in the future the cf will be a
        # sqlite database, this is an important improvement.
        if self.TARGET_DOMAINS is None:
            self.TARGET_DOMAINS = cf.cf.get('target_domains')

        if not response.get_url().get_domain() in self.TARGET_DOMAINS:
            return False

        return self._already_analyzed.add(response.get_uri())
