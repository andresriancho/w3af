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


class progress:
    """
    This class keeps track of the progress of something. Mostly used to keeps
    track of the progress of the w3afCore tests (discovery/audit/etc).
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    """

    def __init__(self):
        self._max_value = 0.0
        self._current_value = 0.0

    def set_total_amount(self, value):
        '''
        Set the max value that the progress "bar" will have.
        '''
        self._max_value = value
        self._current_value = 0.0

    def inc(self):
        '''
        Add 1 unit to the current value.
        '''
        if self._current_value == self._max_value:
            om.out.error('Current value can never be greater than max value!')
        else:
            self._current_value += 1

    def get_progress(self):
        '''
        @return: The % done.
        '''
        # This if is to avoid division by zero
        if self._max_value == 0:
            return 0.0
        
        # This returns the %
        return self._current_value / self._max_value
