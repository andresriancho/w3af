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
import core.controllers.outputManager as om
from core.controllers.threads.threadpool import ThreadPool, WorkRequest
import core.data.kb.config as cf


class threadManager(object):
    '''
    This class manages threads.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    ''' 
    
    def __init__( self ):
        self._daemonThreads = []
        self.informed = False
        self._initialized = False
        self._waitForJoin = 2
        self._initPool()
    
    def _initPool( self ):
        self._maxThreads = cf.cf.getData('maxThreads') or 0
        
        #
        #   Please note that I'm using the q_size parameter of the Threadpool. This is what the 
        #   threadpool documentation says about it:
        #
        #        If q_size > 0 the size of the work request is limited and the
        #       thread pool blocks when queue is full and it tries to put more
        #       work requests in it.
        #
        #   This will basically save me from filling-up all the memory with WorkRequest objects
        #   when somebody performs something like this:
        #
        #   for url in looooooong_list:
        #       self._tm.startFunction( target=self._do_request, args=(url,) )
        #
        if self._maxThreads:
            self._threadPool = ThreadPool(self._maxThreads, q_size = 200)
        else:
            # if I want to use the restrict argument of startFunction, the thread pool 
            # MUST have some threads
            self._threadPool = ThreadPool(5, 15)
    
    def setMaxThreads(self, num_threads):

        if self._maxThreads > num_threads:
            self._threadPool.dismissWorkers(self._maxThreads - num_threads)
            self._maxThreads = num_threads

        elif self._maxThreads < num_threads:
            self._threadPool.createWorkers(num_threads - self._maxThreads)
            self._maxThreads = num_threads

    def getMaxThreads(self):
        if not self._initialized:
            self._initPool()
        return self._maxThreads
        
    def startDaemon(self, threadObj):
        om.out.debug('Starting daemon thread: ' + str(threadObj) )
        threadObj.setDaemon(1)
        threadObj.start()
        self._daemonThreads.append( threadObj )
    
    def stopDaemon( self, threadObj ):
        for daemon in self._daemonThreads:
            if daemon == threadObj:
                threadObj.stop()
                om.out.debug('Calling join on daemon thread: ' + str(threadObj) )
                threadObj.join(self._waitForJoin)
                
    def stopAllDaemons( self ):
        om.out.debug('Calling join on all daemon threads')
        for thread in self._daemonThreads:
            thread.stop()
            om.out.debug('Calling join on daemon thread: ' + str(thread) )
            thread.join(self._waitForJoin)
        
    def startFunction(self, target, args=(), kwds={}, restrict=True, ownerObj=None):
        if not self._initialized:
            self._initPool()
            self._initialized = True
        
        if not self._maxThreads and restrict:
            # Just start the function
            if not self.informed:
                om.out.debug('Threading is disabled.' )
                self.informed = True
            target(*args, **kwds)
        else:
            # Assign a job to a thread in the thread pool
            wr = WorkRequest( target, args=args, kwds=kwds, ownerObj=ownerObj )
            self._threadPool.putRequest( wr )
            msg = '[thread manager] Successfully added function to threadpool. Work queue size: '
            msg += str(self._threadPool.requestsQueue.qsize())
            om.out.debug( msg )
            
    def join( self, ownerObj=None, joinAll=False ):
        self._threadPool.wait( ownerObj, joinAll )

threadManagerObj = threadManager()
