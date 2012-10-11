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
import sys

import core.controllers.outputManager as om

from core.controllers.core_helpers.status import w3af_core_status
from core.controllers.core_helpers.consumers.constants import POISON_PILL
from core.controllers.core_helpers.consumers.base_consumer import BaseConsumer
from core.controllers.exception_handling.helpers import pprint_plugins
from core.controllers.w3afException import w3afException


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
        super(audit, self).__init__(audit_plugins, w3af_core)
        
    def _teardown(self):
        # End plugins
        for plugin in self._consumer_plugins:
            try:
                plugin.end()
            except w3afException, e:
                om.out.error( str(e) )

    def _consume(self, fuzzable_request):
        for plugin in self._consumer_plugins:
            om.out.debug('%s plugin is testing: "%s"' % (plugin.getName(), fuzzable_request ) )
            
            self._add_task()
            
            apply_result = self._threadpool.apply_async( plugin.audit_with_copy,
                                                         (fuzzable_request,),
                                                         callback=self._task_done)
            self._out_queue.put( (plugin.getName(), fuzzable_request, apply_result) )
    
    def handle_audit_results(self):
        '''
        This method handles the results of running audit plugins. The results
        are put() into self._audit_consumer.out_queue by the consumer and they
        are basically the ApplyResult objects from the threadpool.
        
        Since audit plugins don't really return stuff that we're interested in,
        these results are mostly interesting to us because of the exceptions
        that might appear in the plugins. Because of that, the method should be
        called in the main thread and be seen as a way to "bring thread exceptions
        to main thread".
        
        Each time this method is called it will consume all items in the output
        queue. Note that you might have to call this more than once during the
        strategy execution.
        '''
        while True:
            queue_item = self._out_queue.get()

            if queue_item == POISON_PILL:
                break
            else:
                plugin_name, request, apply_result = queue_item
                try:
                    apply_result.get()
                except Exception, e:
                    # Smart error handling, much better than just crashing.
                    # Doing this here and not with something similar to:
                    # sys.excepthook = handle_crash because we want to handle
                    # plugin exceptions in this way, and not framework 
                    # exceptions
                    class fake_status(w3af_core_status):
                        pass
        
                    status = fake_status()
                    status.set_running_plugin( plugin_name, log=False )
                    status.set_phase( 'audit' )
                    status.set_current_fuzzable_request( request )
                    
                    exec_info = sys.exc_info()
                    enabled_plugins = pprint_plugins(self._w3af_core)
                    self._w3af_core.exception_handler.handle( status, e , 
                                                              exec_info,
                                                              enabled_plugins )
                else:
                    # Please note that this is not perfect, it is showing which
                    # plugin result was JUST taken from the Queue. The good thing is
                    # that the "client" reads the status once every 500ms so the user
                    # will see things "moving" and will be happy
                    self._w3af_core.status.set_phase('audit')
                    self._w3af_core.status.set_running_plugin( plugin_name )
                    self._w3af_core.status.set_current_fuzzable_request( request )
        
        om.out.debug('Finished handle_audit_results().')