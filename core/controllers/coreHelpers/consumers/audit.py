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
import threading
import Queue

import core.controllers.outputManager as om

from core.controllers.coreHelpers.consumers.constants import FINISH_CONSUMER

from core.controllers.w3afException import w3afException
from core.controllers.threads.threadpool import Pool


class audit(threading.Thread):
    '''
    Consumer thread that takes fuzzable requests from a Queue that's populated
    by the discovery plugins and identified vulnerabilities by performing various
    requests.
    '''
    
    def __init__(self, in_queue, audit_plugins, w3af_core):
        '''
        @param in_queue: The input queue that will feed the audit plugins
        @param audit_plugins: Instances of audit plugins in a list
        @param w3af_core: The w3af core that we'll use for status reporting
        '''
        super(audit, self).__init__()
        
        self._in_queue = in_queue
        # See documentation in the properly below
        self._out_queue = Queue.Queue()
        self._audit_plugins = audit_plugins
        self._w3af_core = w3af_core
        self._audit_threadpool = Pool(10, queue_size=40)
    
    def run(self):
        '''
        Consume the queue items and find vulnerabilities
        
        TODO:
            * Progress
        '''

        while True:
           
            workunit = self._in_queue.get()

            if workunit == FINISH_CONSUMER:
                
                # Close the pool and wait for everyone to finish
                self._audit_threadpool.poison_all_workers()
                self._audit_threadpool.join()
                
                # End plugins
                for plugin in self._audit_plugins:
                    try:
                        plugin.end()
                    except w3afException, e:
                        om.out.error( str(e) )
                
                # Finish this consumer and everyone consuming the output
                self._out_queue.put( FINISH_CONSUMER )
                break
                
            else:
                
                for plugin in self._audit_plugins:
                    result = self._audit_threadpool.apply_async( plugin.audit_wrapper,
                                                                 (workunit,) )
                    self._out_queue.put( (plugin.getName(), workunit, result) )

    @property
    def out_queue(self):
        #
        #    This output queue can contain one of the following:
        #        * FINISH_CONSUMER
        #        * (plugin_name, fuzzable_request, AsyncResult)
        return self._out_queue
    
    def in_queue_put(self, work):
        return self._in_queue.put( work )
        
    def in_queue_size(self):
        return self._in_queue.qsize()

    def stop(self):
        '''
        Poison the loop
        '''
        self._in_queue.put( FINISH_CONSUMER )
        self._audit_threadpool.join()

