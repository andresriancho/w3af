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
import traceback

import core.data.kb.config as cf
import core.controllers.outputManager as om

from core.controllers.w3afException import (w3afMustStopException,
                                            w3afMustStopByUnknownReasonExc)

        
class ExceptionHandler(object):
    '''
    This class handles exceptions generated while running plugins, usually
    the handling is just to store the traceback for later processing.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    MAX_EXCEPTIONS_PER_PLUGIN = 5
    NO_HANDLING = (MemoryError, w3afMustStopByUnknownReasonExc, w3afMustStopException)
    
    def __init__(self):
        # TODO: Maybe this should be a disk_list just to make sure we don't
        # fill the memory with exceptions?
        self._exception_data = []
        self._lock = threading.RLock()

    def handle( self, current_status, exception, exec_info ):
        '''
        This method stores the current status and the exception for later
        processing. If there are already too many stored exceptions for this
        plugin then no action is taken.
        
        @return: None
        '''
        #
        # There are some exceptions, that because of their nature I don't want
        # to handle. So what I do is to raise them in order for them to get to
        # w3afCore.py , most likely to the except lines around self.strategy.start()
        #
        if isinstance(exception, self.NO_HANDLING):
            raise
            
        stop_on_first_exception = cf.cf.getData( 'stop_on_first_exception' )
        if stop_on_first_exception:
            # TODO: Not sure if this is 100% secure code, but it should work
            # in most cases, and in the worse scenario it is just a developer
            # getting hit ;)
            #
            # The risk is that the exception being raise is NOT the same exception
            # that was caught before calling this handle method. This might happen
            # (not sure actually) in places where lots of exceptions are raised
            # in a threaded environment
            raise
        
        #
        # Now we really handle the exception that was produced by the plugin in
        # the way we want to.
        #
        except_type, except_class, tb = exec_info
        tb = traceback.extract_tb(tb)
        
        with self._lock:
            edata = ExceptionData(current_status, exception, tb)
            
            count = 0
            for stored_edata in self._exception_data:
                if edata.plugin == stored_edata.plugin and\
                edata.phase == stored_edata.phase:
                    count += 1
            
            if count < self.MAX_EXCEPTIONS_PER_PLUGIN:
                self._exception_data.append(edata)

                om.out.information( str(edata) )
                    
        
class ExceptionData(object):
    def __init__(self, current_status, e, tb):
        self.exception = e
        self.traceback = tb
        self.plugin = current_status.get_running_plugin()
        self.phase = current_status.get_phase()
        self.fuzzable_request = current_status.get_current_fuzzable_request()

    def __str__(self):
        res = 'An exception was found while running %s.%s on "%s": "%s". Traceback:\n%s'
        tbstr = '\n'.join([str(i) for i in self.traceback])
        res = res % (self.phase, self.plugin, self.fuzzable_request, self.exception, tbstr)
        return res

exception_handler = ExceptionHandler()
