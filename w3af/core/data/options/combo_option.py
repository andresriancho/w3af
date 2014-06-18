"""
combo_option.py

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
from w3af.core.data.options.baseoption import BaseOption
from w3af.core.data.options.option_types import COMBO


class ComboOption(BaseOption):
    """
    This class represents an ComboOption.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    _type = COMBO

    def __init__(self, name, default_value, desc, _help='', tabid=''):
        """
        :param name: The name of the ComboOption
        :param default_value: The default value of the ComboOption;
                             it is a list of the options that the
                             user can choose from.
        :param desc: The description of the ComboOption
        :param help: The help of the ComboOption; a large description
                     of the ComboOption
        :param tabid: The tab id of the ComboOption
        """
        self._value = default_value[0]
        self._default_value = default_value[0]
        self._combo_options = default_value
        self._name = name
        self._desc = desc
        self._help = _help
        self._tabid = tabid

    def get_combo_options(self):
        return self._combo_options

    def set_value(self, value):
        """
        :param value: The value parameter is set by the user interface, which
                      or example sends 'a' when the options of the combobox are
                      '1','2','a','f'
        """
        self._value = self.validate(value)

    def validate(self, value):
        if value in self._combo_options:
            return value
        else:
            raise BaseFrameworkException('The option you selected is invalid.')
