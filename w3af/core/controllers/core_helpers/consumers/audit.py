"""
audit.py

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

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.core_helpers.consumers.base_consumer import (BaseConsumer,
                                                                        task_decorator)


class audit(BaseConsumer):
    """
    Consumer thread that takes fuzzable requests from a Queue that's populated
    by the crawl plugins and identified vulnerabilities by performing various
    requests.
    """

    def __init__(self, audit_plugins, w3af_core):
        """
        :param audit_plugins: Instances of audit plugins in a list
        :param w3af_core: The w3af core that we'll use for status reporting
        """
        max_qsize = self.THREAD_POOL_SIZE * 2

        super(audit, self).__init__(audit_plugins,
                                    w3af_core,
                                    thread_name='Auditor',
                                    max_pool_queued_tasks=max_qsize,
                                    max_in_queue_size=max_qsize)

    def _teardown(self):
        # End plugins
        for plugin in self._consumer_plugins:
            try:
                plugin.end()
            except BaseFrameworkException, e:
                om.out.error(str(e))
            except Exception, e:
                self.handle_exception('audit', plugin.get_name(),
                                      'plugin.end()', e)

    def get_original_response(self, fuzzable_request):
        plugin = self._consumer_plugins[0]
        return plugin.get_original_response(fuzzable_request)
        
    def _consume(self, fuzzable_request):
        """
        Consume a fuzzable_request that was found by the crawl/infrastructure
        plugins. Basically perform these steps:
        
            * GET the FuzzableRequest and get a handler to the HTTPResponse inst
            * Send the fuzzable_request and http_response instances to all
              plugins in different threads in order for them to work on them
        
        Getting the original response at this level is a performance
        enhancement to avoid sending the same HTTP request many times, once
        for each audit plugin that needed the http_response.
        
        :param fuzzable_request: A FuzzableRequest instance
        """
        try:
            orig_resp = self.get_original_response(fuzzable_request)
        except Exception, e:
            self.handle_exception('audit',
                                  'audit.get_original_response()',
                                  'audit.get_original_response()', e)
            return

        self._run_observers(fuzzable_request)

        for plugin in self._consumer_plugins:
            # Please note that this is not perfect, it is showing which
            # plugin result was JUST taken from the Queue. The good thing is
            # that the "client" reads the status once every 500ms so the user
            # will see things "moving" and will be happy
            self._w3af_core.status.set_running_plugin('audit',
                                                      plugin.get_name())
            self._w3af_core.status.set_current_fuzzable_request('audit',
                                                                fuzzable_request)

            # Note that if we don't limit the input queue size for the thread
            # pool we might end up with a lot of queued calls here! The calls
            # contain an HTTP response body, so they really use a lot of
            # memory!
            #
            # This is controlled by max_pool_queued_tasks
            self._threadpool.apply_async(self._audit,
                                         (plugin, fuzzable_request, orig_resp))

    def _run_observers(self, fuzzable_request):
        """
        Run the observers handling any exception that they might raise
        :return: None
        """
        try:
            for observer in self._observers:
                observer.audit(fuzzable_request)
        except Exception, e:
            self.handle_exception('audit',
                                  'audit._run_observers()',
                                  'audit._run_observers()', e)

    @task_decorator
    def _audit(self, function_id, plugin, fuzzable_request, orig_resp):
        """
        Since threadpool's apply_async runs the callback only when the call to
        this method ends without any exceptions, it is *very important* to
        handle exceptions correctly here. Failure to do so will end up in
        _task_done not called, which will make has_pending_work always return
        True.

        Python 3 has an error_callback in the apply_async method, which we could
        use in the future.
        """
        args = (plugin.get_name(), fuzzable_request.get_uri())
        om.out.debug('%s.audit(%s)' % args)

        start_time = time.time()

        try:
            plugin.audit_with_copy(fuzzable_request, orig_resp)
        except Exception, e:
            self.handle_exception('audit', plugin.get_name(),
                                  fuzzable_request, e)

        spent_time = time.time() - start_time
        args = (plugin.get_name(), fuzzable_request.get_uri(), spent_time)
        om.out.debug('%s.audit(%s) took %.2f seconds to run' % args)
