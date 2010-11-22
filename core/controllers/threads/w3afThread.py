'''
w3afThread.py

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
from core.controllers.threads.threadManager import threadManagerObj as thread_manager
from core.controllers.w3afException import w3afException
import threading

class w3afThread(threading.Thread):
    '''
    This class represents a w3afThread.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    ''' 
    
    def __init__(self):
        threading.Thread.__init__( self )
        self._tm = thread_manager
        
    def stop(self):
        '''
        w3af w3afThreads MUST implment a stop method.
        '''
        raise w3afException('w3af w3afThreads MUST implment a stop method.')
        
    def start2( self ):
        '''
        w3af w3afThreads have this special method.
        '''
        om.out.debug('Called start2() of: ' + str(self) )
        self._tm.startDaemon( self )
        
    def run(self):
        '''
        w3af w3afThreads MUST implement a run method.
        '''
        raise w3afException('w3af w3afThreads MUST implment a run method.')
    

