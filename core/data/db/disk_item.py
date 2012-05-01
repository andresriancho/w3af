'''
disk_item.py

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


class disk_item(object):
    '''
    This is a very simple class that's intented to be a base class for objects
    that want to be stored in a disk_list of disk_set. It basically exposes the
    "get_eq_attrs" method which returns a list with the names of the attributes
    that make this object "unique".
    '''
    def get_eq_attrs(self):
        raise NotImplementedError
