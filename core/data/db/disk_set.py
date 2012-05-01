'''
disk_set.py

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

from core.data.db.disk_list import disk_list


class disk_set(disk_list):
    '''
    A disk_list that only allows to add/append unique items.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        super(disk_set, self).__init__()
        self.__append = super(disk_set, self).append
    
    def add(self, value):
        '''
        Append a value to the disk_set (only if the value is not already contained
        in this instance).
        
        @param value: The value to append.
        @return: True if the value was added. False if it existed and was not added.
        '''
        # thread safe here!
        with self._db_lock:
            if self.__contains__(value):
                return False
            else:
                self.__append(value)
                return True
    
    def update(self, value_list):
        '''
        Extend the disk set with a list of items that is provided in @value_list
        
        @return: None
        '''
        for value in value_list:
            self.add(value)
    
    def extend(self, _):
        raise Exception('Not a valid disk_set method.')

    def append(self, _):
        raise Exception('Not a valid disk_set method.')
