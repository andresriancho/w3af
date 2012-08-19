'''
bruteforce.py

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

from core.controllers.core_helpers.consumers.base_consumer import BaseConsumer
from core.controllers.core_helpers.exception_handler import exception_handler
from core.controllers.w3afException import w3afException
from core.controllers.exception_handling.helpers import pprint_plugins


class bruteforce(BaseConsumer):
    '''
    Consumer thread that takes fuzzable requests from a Queue that's populated
    by the crawl plugins and bruteforces logins by performing various requests.
    '''
    
    def __init__(self, bruteforce_plugins, w3af_core):
        '''
        @param in_queue: The input queue that will feed the bruteforce plugins
        @param bruteforce_plugins: Instances of bruteforce plugins in a list
        @param w3af_core: The w3af core that we'll use for status reporting
        '''
        super(bruteforce, self).__init__(bruteforce_plugins, w3af_core)

    def _teardown(self):
        # End plugins
        for plugin in self._consumer_plugins:
            try:
                plugin.end()
            except w3afException, e:
                om.out.error( str(e) )

    def _consume(self, work_unit):
        for plugin in self._consumer_plugins:
            om.out.debug('%s plugin is testing: "%s"' % (plugin.getName(), work_unit ) )
            result = self._threadpool.apply_async( self._bruteforce,
                                                   (plugin, work_unit,),
                                                   callback=self._task_done)
            self._out_queue.put( (plugin.getName(), work_unit, result) )
            
    def _bruteforce(self, plugin, fuzzable_request):
        '''
        @param fuzzable_request: The fuzzable request that (if suitable) will be
                                 bruteforced by @plugin.
        @return: A list of the URL's that have been successfully bruteforced
        '''
        res = set()
        
        # Status
        om.out.debug('Called _bruteforce(%s,%s)' %(plugin.getName(),fuzzable_request) )
        self._w3af_core.status.set_phase('bruteforce')
        self._w3af_core.status.set_running_plugin( plugin.getName() )
        self._w3af_core.status.set_current_fuzzable_request( fuzzable_request )
        
        # TODO: Report progress to the core.

        try:
            new_frs = plugin.bruteforce_wrapper( fuzzable_request )
        except w3afException, e:
            om.out.error( str(e) )
        
        except Exception, e:
            # Smart error handling, much better than just crashing.
            # Doing this here and not with something similar to:
            # sys.excepthook = handle_crash because we want to handle
            # plugin exceptions in this way, and not framework 
            # exceptions                    
            exec_info = sys.exc_info()
            enabled_plugins = pprint_plugins(self._w3af_core)
            exception_handler.handle( self._w3af_core.status, e , 
                                      exec_info, enabled_plugins )
        
        else:
            res.update( new_frs )
                
        return res
