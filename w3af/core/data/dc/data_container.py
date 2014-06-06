# -*- coding: utf-8 -*-
"""
data_container.py

Copyright 2014 Andres Riancho

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
from w3af.core.data.db.disk_item import DiskItem
from w3af.core.data.constants.encodings import UTF8


class DataContainer(DiskItem):
    MAX_PRINTABLE = 65

    def __init__(self, encoding=UTF8):
        super(DataContainer, self).__init__()
        self.encoding = encoding
        self.token = None

    def _to_str_with_separators(self, key_val_sep, pair_sep):
        """
        :warning: The subclass needs to implement it
        """
        raise NotImplementedError

    def get_token(self):
        return self.token

    def set_token(self, *args):
        """
        Sets the token in the DataContainer to point to the variable specified
        in *args. Usually args will be one of:
            * ('id',) - When the data container doesn't support repeated params
            * ('id', 3) - When it does

        :raises: An exception when the DataContainer does NOT contain the
                 specified path in *args to find the variable
        :return: The token if we were able to set it in the DataContainer
        """
        raise NotImplementedError

    def get_short_printable_repr(self):
        """
        :return: A string with a short printable representation of self which is
                 shorter in length than MAX_PRINTABLE
        """
        raise NotImplementedError

    @property
    def all_items(self):
        return str(self)

    def get_eq_attrs(self):
        return ['all_items']
