'''
threadManager.py

Copyright 2006 Andres Riancho

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
import Queue

import core.controllers.outputManager as om

from core.controllers.threads.threadpool import Pool


class ThreadManager(object):
    '''
    This class manages threads.
    
    Note: This is just a wrapper around Pool 
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    ''' 
    
    MAX_THREADS = 20
    
    def __init__( self ):
        self._informed = False
        self._initialized = False
        # FIXME: Remove me (and potentially the whole threadmanager object)
        self._results = {}
    
    def _init_pool( self ):
        self._max_threads = self.MAX_THREADS
        self.threadpool = Pool(self._max_threads, queue_size=200)
        
    def apply_async(self, target, args=(), kwds={}, ownerObj=None):
        
        assert len(kwds) == 0, 'The new ThreadPool does NOT support kwds.'
        
        if not self._initialized:
            self._init_pool()
            self._initialized = True
        
        result = self.threadpool.apply_async(target, args)
        self._results.setdefault(ownerObj, Queue.Queue() ).put(result)
                
        msg = '[thread manager] Successfully added function to threadpool.'
        msg += 'Work queue size: %s' % self.threadpool.in_qsize()
        om.out.debug( msg )
            
    def join( self, ownerObj=None, joinAll=False ):
        
        if joinAll:
            to_join = self._results.keys()
        else:
            to_join = [ownerObj,]
        
        for owner_obj in to_join:

            while True:
                try:
                    result = self._results[owner_obj].get_nowait()
                except Queue.Empty:
                    del self._results[owner_obj]
                    break
                except KeyError:
                    break
                else:
                    result.get()
        
    
    def terminate(self):
        self.threadpool.terminate()


thread_manager = ThreadManager()
