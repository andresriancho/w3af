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
        self.started = False
        
        # FIXME: Remove me (and potentially the whole threadmanager object)
        self._results = {}
    
    @property
    def threadpool(self):
        if not self.started:
            self.start()
        return self._threadpool
    
    def start( self ):
        self._threadpool = Pool(self.MAX_THREADS, queue_size=200)
        
    def apply_async(self, target, args=(), kwds={}, ownerObj=None):
        
        assert len(kwds) == 0, 'The new ThreadPool does NOT support kwds.'

        if not self.started:
            self.started = True
            self.start()
        
        result = self._threadpool.apply_async(target, args)
        self._results.setdefault(ownerObj, Queue.Queue() ).put(result)
                
        msg = '[thread manager] Successfully added function to threadpool.'
        msg += 'Work queue size: %s' % self._threadpool.in_qsize()
        om.out.debug( msg )
            
    def join( self, ownerObj=None):
        
        if ownerObj is None:
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
        if self.started:
            self._threadpool.terminate()
            self.started = False

class one_to_many(object):
    '''
    This is a simple wrapper that translates one argument to many in a function
    call. Useful for passing to the threadpool map function.
    '''
    def __init__(self, func):
        self.func = func
    
    def __call__(self, args):
        return self.func(*args)

thread_manager = ThreadManager()
