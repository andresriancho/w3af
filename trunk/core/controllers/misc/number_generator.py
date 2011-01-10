'''
number_generator.py

Copyright 2009 Andres Riancho

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

from __future__ import with_statement
import thread


class number_generator(object):
    '''
    The simplest class that returns a sequence of consecutive numbers.
    
    This is used for assigning IDs to HTTP request and responses.
    '''
    
    def __init__(self):
        '''
        Start the counter and be thread safe.
        '''
        self._lock = thread.allocate_lock()
        self._id = 0
        
    def inc(self):
        '''
        @return: The next number.
        '''
        with self._lock:
            self._id += 1
            return self._id
            
    def get(self):
        '''
        @return: The current number
        '''
        return self._id
    
    def reset(self):
        '''
        Reset internal counter to 0.
        '''
        with self._lock:
            self._id = 0
            
consecutive_number_generator = number_generator()
