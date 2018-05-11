"""
disk_item.py

Copyright 2012 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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

"""


class DiskItem(object):
    """
    This is a very simple class that's intended to be a base class for objects
    that want to be stored in a DiskList of DiskSet.
    """
    __slots__ = ()

    def get_eq_attrs(self):
        """
        The DiskList class will use the values associated with the attributes
        listed in the response of get_eq_attrs() to calculate an md5, which
        is saved to the DB, indexed, and then used to have a fast(er)
        __contains__ implementation

        :return: A list with the attributes of the subclass that make it
                 "unique". In most cases all attributes which have data
                 that can't be calculated based on other attributes.
        """
        raise NotImplementedError
