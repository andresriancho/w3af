"""
bruteforce.py

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

from w3af.core.controllers.core_helpers.consumers.base_consumer import (BaseConsumer,
                                                                        task_decorator)
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.threads.threadpool import return_args


class bruteforce(BaseConsumer):
    """
    Consumer thread that takes fuzzable requests from a Queue that's populated
    by the crawl plugins and bruteforces logins by performing various requests.
    """

    def __init__(self, bruteforce_plugins, w3af_core):
        """
        :param bruteforce_plugins: Instances of bruteforce plugins in a list
        :param w3af_core: The w3af core that we'll use for status reporting
        """
        super(bruteforce, self).__init__(bruteforce_plugins, w3af_core,
                                         thread_name='Bruteforcer')

    def _teardown(self):
        # End plugins
        for plugin in self._consumer_plugins:
            try:
                plugin.end()
            except BaseFrameworkException, e:
                om.out.error(str(e))

    def _run_observers(self, fuzzable_request):
        """
        Run the observers handling any exception that they might raise
        :return: None
        """
        try:
            for observer in self._observers:
                observer.bruteforce(fuzzable_request)
        except Exception, e:
            self.handle_exception('bruteforce',
                                  'bruteforce._run_observers()',
                                  'bruteforce._run_observers()', e)

    @task_decorator
    def _consume(self, function_id, work_unit):
        self._run_observers(work_unit)

        for plugin in self._consumer_plugins:
            self._threadpool.apply_async(return_args(self._bruteforce),
                                         (plugin, work_unit,),
                                         callback=self._plugin_finished_cb)

    def _plugin_finished_cb(self, ((plugin, input_fuzzable_request), plugin_result)):
        for new_fuzzable_request in plugin_result:
            self._out_queue.put((plugin.get_name(),
                                 input_fuzzable_request,
                                 new_fuzzable_request))

    @task_decorator
    def _bruteforce(self, function_id, plugin, fuzzable_request):
        """
        Since threadpool's apply_async runs the callback only when the call to
        this method ends without any exceptions, it is *very important* to
        handle exceptions correctly here. Failure to do so will end up in
        _task_done not called, which will make has_pending_work always return
        True.

        Python 3 has an error_callback in the apply_async method, which we could
        use in the future.

        :param fuzzable_request: The fuzzable request that (if suitable) will be
                                 bruteforced by @plugin.
        :return: A list of the URL's that have been successfully bruteforced
        """
        res = set()

        # Logging
        args = (plugin.get_name(), fuzzable_request.get_uri())
        om.out.debug('%s.bruteforce(%s)' % args)
        start_time = time.time()

        # Status
        self._w3af_core.status.set_running_plugin('bruteforce', plugin.get_name())
        self._w3af_core.status.set_current_fuzzable_request('bruteforce',
                                                            fuzzable_request)

        # TODO: Report progress to the core.
        try:
            new_frs = plugin.bruteforce_wrapper(fuzzable_request)
        except Exception, e:
            self.handle_exception('bruteforce', plugin.get_name(),
                                  fuzzable_request, e)
        else:
            res.update(new_frs)

        spent_time = time.time() - start_time
        args = (plugin.get_name(), fuzzable_request.get_uri(), spent_time)
        om.out.debug('%s.bruteforce(%s) took %.2f seconds to run' % args)

        return res
