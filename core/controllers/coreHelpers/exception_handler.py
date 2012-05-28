'''
exception_handler.py

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

import core.data.kb.config as cf
     
        
class ExceptionHandler(object):
    '''
    This class handles exceptions generated while running plugins, usually
    the handling is just to store the traceback for later processing.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    MAX_EXCEPTIONS_PER_PLUGIN = 5
    
    def __init__(self):
        # TODO: Maybe this should be a disk_list just to make sure we don't
        # fill the memory with exceptions?
        self._exception_data = []
        self._lock = threading.RLock()

    def handle( self, current_status, exception ):
        '''
        This method stores the current status and the exception for later
        processing. If there are already too many stored exceptions for this
        plugin then no action is taken.
        
        @return: None
        '''
        stop_on_first_exception = cf.cf.getData( 'stop_on_first_exception' )
        if stop_on_first_exception:
            # TODO: BUGBUG: I'm I loosing the traceback information here? 
            raise exception
        
        else:
        
            with self._lock:
                edata = ExceptionData(e, current_status)
                
                count = 0
                for stored_edata in self._exception_data:
                    if edata.plugin == stored_edata.plugin and\
                    edata.phase == stored_edata.phase:
                        count += 1
                
                if count < self.MAX_EXCEPTIONS_PER_PLUGIN:
                    self._exception_data.append(edata)
            
        
class ExceptionData(object):
    def __init__(self, e, current_status):
        self.exception = e
        self.plugin = current_status.get_running_plugin()
        self.phase = current_status.get_phase()
        self.fuzzable_request = current_status.get_current_fuzzable_request()


exception_handler = ExceptionHandler()
