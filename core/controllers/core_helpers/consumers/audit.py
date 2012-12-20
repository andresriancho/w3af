'''
audit.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
import core.controllers.output_manager as om

from core.controllers.core_helpers.consumers.base_consumer import BaseConsumer
from core.controllers.exceptions import w3afException


class audit(BaseConsumer):
    '''
    Consumer thread that takes fuzzable requests from a Queue that's populated
    by the crawl plugins and identified vulnerabilities by performing various
    requests.
    '''

    def __init__(self, audit_plugins, w3af_core):
        '''
        @param in_queue: The input queue that will feed the audit plugins
        @param audit_plugins: Instances of audit plugins in a list
        @param w3af_core: The w3af core that we'll use for status reporting
        '''
        super(audit, self).__init__(audit_plugins, w3af_core,
                                    thread_name='Auditor')

    def _teardown(self):
        # End plugins
        for plugin in self._consumer_plugins:
            try:
                plugin.end()
            except w3afException, e:
                om.out.error(str(e))
            except Exception, e:
                self.handle_exception('audit', plugin.get_name(), 'plugin.end()', e)                

    def _consume(self, fuzzable_request):
        for plugin in self._consumer_plugins:
            om.out.debug('%s plugin is testing: "%s"' % (plugin.get_name(),
                                                         fuzzable_request))

            # Please note that this is not perfect, it is showing which
            # plugin result was JUST taken from the Queue. The good thing is
            # that the "client" reads the status once every 500ms so the user
            # will see things "moving" and will be happy
            self._w3af_core.status.set_phase('audit')
            self._w3af_core.status.set_running_plugin(plugin.get_name())
            self._w3af_core.status.set_current_fuzzable_request(
                fuzzable_request)

            self._threadpool.apply_async(self._audit,
                                        (plugin, fuzzable_request,))

    def _audit(self, plugin, fuzzable_request):
        '''
        Since threadpool's apply_async runs the callback only when the call to
        this method ends without any exceptions, it is *very important* to handle
        exceptions correctly here. Failure to do so will end up in _task_done not
        called, which will make has_pending_work always return True.

        Python 3 has an error_callback in the apply_async method, which we could
        use in the future.
        '''
        self._add_task()
        try:
            plugin.audit_with_copy(fuzzable_request)
        except Exception, e:
            self.handle_exception('audit', plugin.get_name(),
                                  fuzzable_request, e)
        finally:
            self._task_done(None)
