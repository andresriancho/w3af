'''
progress.py

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
import time

class progress:
    """
    This class keeps track of the progress of something. Mostly used to keeps
    track of the progress of the w3afCore tests (discovery/audit/etc).
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    """

    def __init__(self):
        self._max_value = 0.0
        self._current_value = 0.0
        self._first_amount_change_time = None
        self._eta = None

    def set_total_amount(self, value):
        '''
        Set the max value that the progress "bar" will have.
        '''
        self._max_value = value
        self._current_value = 0.0
        self._first_amount_change_time = None
        
    def inc(self):
        '''
        Add 1 unit to the current value.
        >>> p = progress()
        >>> p.set_total_amount(100)
        >>> p.inc()
        >>> p.get_progress()
        0.01
                
        '''
        if self._current_value == self._max_value:
            om.out.error('Current value can never be greater than max value!')
        else:
            # inc the counter
            self._current_value += 1
            self._update_eta()
            
    def _update_eta(self):
        # handle the time stuff
        if not self._first_amount_change_time:
            self._first_amount_change_time = time.time()
        else:
            time_already_elapsed = time.time() - self._first_amount_change_time
            #
            # Simple calculation to find out how much time it is going to take
            #
            try:
                time_for_all_requests = ( self._max_value * time_already_elapsed ) / self._current_value
            except ZeroDivisionError:
                # I should never get here...
                time_for_all_requests = time_already_elapsed * self._max_value * 2
            else:
                self._eta = time_for_all_requests - time_already_elapsed

    def get_progress(self):
        '''
        @return: The % done.
        
        >>> p = progress()
        >>> p.get_progress()
        0.0
        
        >>> p.set_total_amount(10)
        >>> p.get_progress()
        0.0
        
        >>> p.stop()
        >>> p.get_progress()
        0.0
        '''
        # This if is to avoid division by zero
        if self._max_value == 0:
            return 0.0
        
        # This returns the %
        return self._current_value / self._max_value

    def stop(self):
        '''
        This method is called from the core to indicate that the scan process has been stopped
        by the user, or an error has been found.
        '''
        self._max_value = 0.0
        self._current_value = 0.0
        self._first_amount_change_time = None
        self._eta = None

    def get_eta(self):
        '''
        @return: The ETA for this phase.
        '''
        if not self._eta:
            return 0, 0, 0, 0
        else:
            # recalculate the value
            self._update_eta()
            
            temp = float()
            temp = float(self._eta) / (60*60*24)
            d    = int(temp)
            temp = (temp - d) * 24
            h = int(temp)
            temp = (temp - h) * 60
            m = int(temp)
            temp = (temp - m) * 60
            sec = temp
            return d,h,m,sec
