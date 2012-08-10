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
from multiprocessing.dummy import Queue, Process

import core.controllers.outputManager as om

from core.controllers.coreHelpers.consumers.constants import FINISH_CONSUMER
from core.controllers.threads.threadpool import Pool
from core.controllers.w3afException import w3afException


class audit(Process):
    '''
    Consumer thread that takes fuzzable requests from a Queue that's populated
    by the crawl plugins and identified vulnerabilities by performing various
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
        # See documentation in the property below
        self._out_queue = Queue()
        self._audit_plugins = audit_plugins
        self._w3af_core = w3af_core
        self._audit_threadpool = Pool(10)
    
    def run(self):
        '''
        Consume the queue items and find vulnerabilities
        
        TODO: Report progress to w3afCore somehow.
        '''

        while True:
           
            workunit = self._in_queue.get()

            if workunit == FINISH_CONSUMER:
                
                # Close the pool and wait for everyone to finish
                self._audit_threadpool.close()
                self._audit_threadpool.join()
                
                # End plugins
                
                for plugin in self._audit_plugins:
                    try:
                        plugin.end()
                    except w3afException, e:
                        om.out.error( str(e) )
                
                # Finish this consumer and everyone consuming the output
                self._out_queue.put( FINISH_CONSUMER )
                self._in_queue.task_done()
                break
                
            else:
                
                for plugin in self._audit_plugins:
                    om.out.debug('%s plugin is testing: "%s"' % (plugin.getName(), workunit ) )
                    result = self._audit_threadpool.apply_async( plugin.audit_wrapper,
                                                                 (workunit,) )
                    self._out_queue.put( (plugin.getName(), workunit, result) )
            
                self._in_queue.task_done()

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

    def join(self):
        '''
        Poison the loop and wait for all queued work to finish this might take
        some time to process.
        '''
        self._in_queue.put( FINISH_CONSUMER )
        self._in_queue.join()

    def terminate(self):
        '''
        Remove all queued work from in_queue and poison the loop so the consumer
        exits. Should be very fast and called only if we don't care about the
        queued work anymore (ie. user clicked stop in the UI).
        '''
        while not self._in_queue.empty():
            self._in_queue.get()
            self._in_queue.task_done()
        
        self._in_queue.put( FINISH_CONSUMER )
        self._in_queue.join()

