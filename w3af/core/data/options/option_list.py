"""
option_list.py

Copyright 2008 Andres Riancho

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
from w3af.core.controllers.exceptions import BaseFrameworkException


class OptionList(object):
    """
    This class represents a list of options.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        self._internal_opt_list = []

    def add(self, option):
        self._internal_opt_list.append(option)
    append = add

    def __len__(self):
        return len(self._internal_opt_list)

    def __repr__(self):
        """
        A nice way of printing your object =)
        """
        return '<OptionList: ' + '|'.join([i.get_name() for i in self._internal_opt_list]) + '>'

    def __eq__(self, other):
        if not isinstance(other, OptionList):
            return False

        return self._internal_opt_list == other._internal_opt_list

    def __contains__(self, item_name):
        for o in self._internal_opt_list:
            if o.get_name() == item_name:
                return True
        return False

    def __getitem__(self, item_name):
        """
        This method is used when on any configurable object the developer does
        something like:

        def set_options( self, optionsList ):
            self._check_persistent = optionsList['check_persistent']

        :return: The value of the item that was selected

        >>> from w3af.core.data.options.opt_factory import opt_factory
        >>> opt_list = OptionList()
        >>> opt_list.add( opt_factory('name', True, 'desc', 'boolean') )
        >>> opt_list['name']
        <option name:name|type:boolean|value:True>

        """
        try:
            item_name = int(item_name)
        except:
            # A string
            for o in self._internal_opt_list:
                if o.get_name() == item_name:
                    return o
            else:
                msg = ('The OptionList doesn\'t contain an option with the'
                       ' name: "%s"')
                raise BaseFrameworkException(msg % item_name)
        else:
            # An integer
            return self._internal_opt_list[item_name]
