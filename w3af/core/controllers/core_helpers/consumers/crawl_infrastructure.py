"""
crawl_infrastructure.py

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
import Queue
import time

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.config as cf
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.data.db.variant_db import VariantDB
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.request.fuzzable_request import FuzzableRequest

from w3af.core.controllers.core_helpers.consumers.constants import POISON_PILL
from w3af.core.controllers.exceptions import BaseFrameworkException, RunOnce
from w3af.core.controllers.threads.threadpool import return_args
from w3af.core.controllers.core_helpers.consumers.base_consumer import (BaseConsumer,
                                                                        task_decorator)


class crawl_infrastructure(BaseConsumer):
    """
    Consumer thread that takes fuzzable requests from the input Queue that is
    seeded by the core, sends each fr to all crawl and infrastructure plugins,
    get()'s the output from those plugins and puts them in the input Queue
    again for continuing with the discovery process.
    """

    def __init__(self, crawl_infrastructure_plugins, w3af_core,
                 max_discovery_time):
        """
        :param crawl_infrastructure_plugins: Instances of crawl_infrastructure
                                             plugins in a list
        :param w3af_core: The w3af core that we'll use for status reporting
        :param max_discovery_time: The max time (in seconds) to use for the
                                   discovery phase
        """
        super(crawl_infrastructure, self).__init__(crawl_infrastructure_plugins,
                                                   w3af_core,
                                                   thread_name='CrawlInfra',
                                                   max_pool_queued_tasks=100)
        self._max_discovery_time = int(max_discovery_time)

        # For filtering fuzzable requests found by plugins:
        self._variant_db = VariantDB()

        self._disabled_plugins = set()
        self._running = True
        self._report_max_time = True
        self._reported_found_urls = ScalableBloomFilter()

    def run(self):
        """
        Consume the queue items, sending them to the plugins which are then
        going to find vulnerabilities, new URLs, etc.
        """
        while True:

            try:
                work_unit = self.in_queue.get(timeout=0.1)
            except KeyboardInterrupt:
                # https://github.com/andresriancho/w3af/issues/9587
                #
                # If we don't do this, the thread will die and will never
                # process the POISON_PILL, which will end up in an endless
                # wait for .join()
                continue

            except Queue.Empty:
                # pylint: disable=E1120
                try:
                    self._route_all_plugin_results()
                except KeyboardInterrupt:
                    continue
                # pylint: enable=E1120
            else:
                if work_unit == POISON_PILL:

                    # Close the pool and wait for everyone to finish
                    self._threadpool.close()
                    self._threadpool.join()
                    del self._threadpool
                    self._running = False
                    self._teardown()

                    # Finish this consumer and everyone consuming the output
                    self._out_queue.put(POISON_PILL)
                    self.in_queue.task_done()
                    break

                else:
                    # With specific error/success handling just for debugging
                    try:
                        self._consume(work_unit)
                    except KeyboardInterrupt:
                        self.in_queue.task_done()
                    except:
                        self.in_queue.task_done()
                    else:
                        self.in_queue.task_done()

                    work_unit = None

    def _teardown(self, plugin=None):
        """
        End plugins
        """
        if plugin is None:
            to_teardown = self._consumer_plugins
        else:
            to_teardown = [plugin, ]

        # When we disable a plugin, we call .end() , so no need to call the
        # same method twice
        to_teardown = set(to_teardown) - self._disabled_plugins

        for plugin in to_teardown:
            try:
                plugin.end()
            except BaseFrameworkException, e:
                om.out.error('The plugin "%s" raised an exception in the '
                             'end() method: %s' % (plugin.get_name(), e))

    @task_decorator
    def _consume(self, function_id, work_unit):
        for plugin in self._consumer_plugins:

            if not self._running:
                return

            if plugin in self._disabled_plugins:
                continue

            self._run_observers(work_unit)

            # TODO: unittest what happens if an exception (which is not handled
            #       by the exception handler) is raised. Who's doing a .get()
            #       on those ApplyResults generated here?
            self._threadpool.apply_async(return_args(self._discover_worker),
                                         (plugin, work_unit,),
                                         callback=self._plugin_finished_cb)
            # pylint: disable=E1120
            self._route_all_plugin_results()
            # pylint: enable=E1120

    def _run_observers(self, fuzzable_request):
        """
        Run the observers handling any exception that they might raise
        :return: None
        """
        try:
            for observer in self._observers:
                observer.crawl(fuzzable_request)
        except Exception, e:
            self.handle_exception('crawl_infrastructure',
                                  'crawl_infrastructure._run_observers()',
                                  'crawl_infrastructure._run_observers()', e)

    @task_decorator
    def _plugin_finished_cb(self,
                            function_id,
                            ((plugin, fuzzable_request), plugin_result)):
        if not self._running:
            return

        # pylint: disable=E1120
        self._route_plugin_results(plugin)
        # pylint: enable=E1120

    @task_decorator
    def _route_all_plugin_results(self, function_id):
        for plugin in self._consumer_plugins:

            if not self._running:
                return

            if plugin in self._disabled_plugins:
                continue

            # pylint: disable=E1120
            self._route_plugin_results(plugin)
            # pylint: enable=E1120

    @task_decorator
    def _route_plugin_results(self, function_id, plugin):
        """
        Retrieve the results from all plugins and put them in our output Queue.
        """
        while True:

            try:
                fuzzable_request = plugin.output_queue.get_nowait()
            except Queue.Empty:
                break

            else:
                # Is the plugin really returning a fuzzable request?
                if not isinstance(fuzzable_request, FuzzableRequest):
                    msg = 'The %s plugin did NOT return a FuzzableRequest.'
                    ve = ValueError(msg % plugin.get_name())
                    self.handle_exception(plugin.get_type(), plugin.get_name(),
                                          fuzzable_request, ve)


                # The plugin has queued some results and now we need to analyze
                # which of the returned fuzzable requests are new and should be
                # put in the input_queue again.
                elif self._is_new_fuzzable_request(plugin, fuzzable_request):

                    # Update the list / set that lives in the KB
                    kb.kb.add_fuzzable_request(fuzzable_request)

                    self._out_queue.put((plugin.get_name(),
                                         None,
                                         fuzzable_request))

            finally:
                # Should I continue with the crawl phase? If not, simply call
                # terminate() to clear the input queue and put a POISON_PILL
                # in the output queue
                if self._should_stop_discovery():
                    self._running = False
                    self._force_end()
                    break

    def _force_end(self):
        """
        I had to create this method in order to be able to quickly end the
        discovery phase from within the same thread.
        """
        # Clear all items in the input queue so no more work is performed
        while not self.in_queue.empty():
            self.in_queue.get()
            self.in_queue.task_done()

        # Let the client know that I finished
        self.out_queue.put(POISON_PILL)

    def join(self):
        super(crawl_infrastructure, self).join()
        self.cleanup()
        self.show_summary()

    def cleanup(self):
        """
        Remove the crawl and bruteforce plugins from memory.
        """
        self._w3af_core.plugins.plugins['crawl'] = []
        self._w3af_core.plugins.plugins['infrastructure'] = []

        self._disabled_plugins = set()
        self._consumer_plugins = []

        self._variant_db.cleanup()

    def show_summary(self):
        """
        This method is called after the crawl and infrastructure phases finishes
        and reports identified URLs and fuzzable requests to the user.
        """
        if not len(kb.kb.get_all_known_urls()):
            om.out.information('No URLs found during crawl phase.')
            return

        # Sort URLs
        tmp_url_list = list(set(kb.kb.get_all_known_urls()))

        all_known_fuzzable_requests = kb.kb.get_all_known_fuzzable_requests()

        msg = 'Found %s URLs and %s different injections points.'
        msg = msg % (len(tmp_url_list),
                     len(all_known_fuzzable_requests))
        om.out.information(msg)

        # print the URLs
        om.out.information('The URL list is:')

        tmp_url_list = ['- %s' % u.url_string for u in tmp_url_list]
        tmp_url_list.sort()
        map(om.out.information, tmp_url_list)

        # Now I simply print the list that I have after the filter.
        om.out.information('The list of fuzzable requests is:')

        tmp_fr = [u'- %s' % unicode(fr) for fr in all_known_fuzzable_requests]
        tmp_fr.sort()
        map(om.out.information, tmp_fr)

    def _should_stop_discovery(self):
        """
        :return: True if we should stop the crawl phase because of time limit
                 set by the user, or simply because the user wants to stop the
                 crawl phase.
        """
        if not self._running:
            return True

        if self._w3af_core.status.get_run_time() > self._max_discovery_time:
            if self._report_max_time:
                self._report_max_time = False
                msg = ('Maximum crawl time limit hit, no new URLs will be'
                       ' added to the queue.')
                om.out.information(msg)
            return True

        return False

    def _remove_discovery_plugin(self, plugin_to_remove):
        """
        Remove plugins that don't want to be run anymore and raised a RunOnce
        exception during the crawl phase.
        """
        for plugin_type in ('crawl', 'infrastructure'):
            if plugin_to_remove in self._w3af_core.plugins.plugins[plugin_type]:

                msg = 'The %s plugin: "%s" wont be run anymore.'
                om.out.debug(msg % (plugin_type, plugin_to_remove.get_name()))

                # Add it to the list of disabled plugins, and run the end()
                # method
                self._disabled_plugins.add(plugin_to_remove)
                self._teardown(plugin_to_remove)

                # TODO: unittest that they are really disabled after adding them
                #       to the disabled_plugins set.
                break

    def _is_new_fuzzable_request(self, plugin, fuzzable_request):
        """
        :param plugin: The plugin that found these fuzzable requests
        :param fuzzable_request: A potentially new fuzzable request

        :return: True if @FuzzableRequest is new (never seen before).
        """
        base_urls_cf = cf.cf.get('baseURLs')
        fr_uri = fuzzable_request.get_uri()

        # Is the "new" fuzzable request domain in the configured targets?
        if fr_uri.base_url() not in base_urls_cf:
            return False

        # Filter out the fuzzable requests that aren't important
        # (and will be ignored by audit plugins anyway...)
        #
        #   What I want to do here, is filter the repeated fuzzable requests.
        #   For example, if the spidering process found:
        #       - http://host.tld/?id=3739286
        #       - http://host.tld/?id=3739285
        #       - http://host.tld/?id=3739282
        #       - http://host.tld/?id=3739212
        #
        # I don't want to have all these different fuzzable requests. The
        # reason is that audit plugins will try to send the payload to each
        # parameter, thus generating the following requests:
        #       - http://host.tld/?id=payload1
        #       - http://host.tld/?id=payload1
        #       - http://host.tld/?id=payload1
        #       - http://host.tld/?id=payload1
        #
        # w3af has a cache, but its still a waste of time to send those requests.
        #
        #   Now lets analyze this with more than one parameter. Spidered URIs:
        #       - http://host.tld/?id=3739286&action=create
        #       - http://host.tld/?id=3739285&action=create
        #       - http://host.tld/?id=3739282&action=remove
        #       - http://host.tld/?id=3739212&action=remove
        #
        #   Generated requests:
        #       - http://host.tld/?id=payload1&action=create
        #       - http://host.tld/?id=3739286&action=payload1
        #       - http://host.tld/?id=payload1&action=create
        #       - http://host.tld/?id=3739285&action=payload1
        #       - http://host.tld/?id=payload1&action=remove
        #       - http://host.tld/?id=3739282&action=payload1
        #       - http://host.tld/?id=payload1&action=remove
        #       - http://host.tld/?id=3739212&action=payload1
        #
        #   In cases like this one, I'm sending these repeated requests:
        #       - http://host.tld/?id=payload1&action=create
        #       - http://host.tld/?id=payload1&action=create
        #       - http://host.tld/?id=payload1&action=remove
        #       - http://host.tld/?id=payload1&action=remove
        #
        if not self._variant_db.append(fuzzable_request):
            msg = 'Ignoring reference "%s" (it is simply a variant).'
            msg %= fuzzable_request.get_uri()
            om.out.debug(msg)
            return False

        msg = 'New fuzzable request identified: "%s"'
        om.out.debug(msg % fuzzable_request)

        # Log the new finding to the user, without dups
        # https://github.com/andresriancho/w3af/issues/8496
        url = fuzzable_request.get_url()
        if self._reported_found_urls.add(url):
            msg = 'New URL found by %s plugin: "%s"'
            args = (plugin.get_name(), url)
            om.out.information(msg % args)

        return True

    @task_decorator
    def _discover_worker(self, function_id, plugin, fuzzable_request):
        """
        This method runs @plugin with FuzzableRequest as parameter and returns
        new fuzzable requests and/or stores vulnerabilities in the knowledge
        base.

        Since threadpool's apply_async runs the callback only when the call to
        this method ends without any exceptions, it is *very important* to
        handle exceptions correctly here. Failure to do so will end up in
        _task_done not called, which will make has_pending_work always return
        True.

        Python 3 has an error_callback in the apply_async method, which we could
        use in the future.

        TODO: unit-test this method

        :return: A list with the newly found fuzzable requests.
        """
        args = (plugin.get_name(), fuzzable_request.get_uri())
        om.out.debug('%s.discover(%s)' % args)

        start_time = time.time()

        # Status reporting
        status = self._w3af_core.status
        status.set_running_plugin('crawl', plugin.get_name())
        status.set_current_fuzzable_request('crawl', fuzzable_request)
        om.out.debug('%s is testing "%s"' % (plugin.get_name(),
                                             fuzzable_request.get_uri()))

        try:
            result = plugin.discover_wrapper(fuzzable_request)
        except BaseFrameworkException, e:
            msg = 'An exception was found while running "%s" with "%s": "%s".'
            om.out.error(msg % (plugin.get_name(), fuzzable_request), e)
        except RunOnce:
            # Some plugins are meant to be run only once
            # that is implemented by raising a RunOnce
            # exception
            self._remove_discovery_plugin(plugin)
        except Exception, e:
            self.handle_exception(plugin.get_type(), plugin.get_name(),
                                  fuzzable_request, e)
        else:
            # The plugin output is retrieved and analyzed by the
            # _route_plugin_results method, here we just verify that the plugin
            # result is None (which proves that the plugin respects this part
            # of the API)
            if result is not None:
                msg = 'The %s plugin did NOT return None.' % plugin.get_name()
                ve = ValueError(msg)
                self.handle_exception(plugin.get_type(), plugin.get_name(),
                                      fuzzable_request, ve)

        spent_time = time.time() - start_time
        args = (plugin.get_name(), fuzzable_request.get_uri(), spent_time)
        om.out.debug('%s.discover(%s) took %.2f seconds to run' % args)
