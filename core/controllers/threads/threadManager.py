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
    This class manages threads. Note: This is just a wrapper around Pool 
    
    @author: Andres Riancho (andres.riancho@gmail.com)
    ''' 
    
    MAX_THREADS = 20
    
    def __init__( self ):
        self._threadpool = None
        
        # FIXME: Remove me (and potentially the whole threadmanager object)
        self._results = {}
    
    @property
    def threadpool(self):
        if self._threadpool is None:
            self.start()
        return self._threadpool
    
    def start( self ):
        self._threadpool = Pool(self.MAX_THREADS)
        
    def apply_async(self, target, args=(), kwds={}, ownerObj=None):
        
        assert len(kwds) == 0, 'The new ThreadPool does NOT support kwds.'

        if self._threadpool is None:
            self.start()
        
        result = self._threadpool.apply_async(target, args)
        self._results.setdefault(ownerObj, Queue.Queue() ).put(result)
                
        msg = '[thread manager] Successfully added function to threadpool.'
        msg += 'Work queue size: %s' % self._threadpool.in_qsize()
        om.out.debug( msg )
            
    def join( self, ownerObj=None):
        if self._threadpool is None:
            return
        
        if ownerObj is None:
            # Means that I want to join all the threads
            self._threadpool.join()
            self._results = {}
            
        else:
            # Only join the threads that were created for ownerObj
            while True:
                try:
                    result = self._results[ownerObj].get_nowait()
                except Queue.Empty:
                    del self._results[ownerObj]
                    break
                except KeyError:
                    break
                else:
                    result.get()
            
    
    def terminate(self):
        if self._threadpool is not None:
            self._threadpool.terminate()
            self._threadpool = None

thread_manager = ThreadManager()
