"""
configurable.py

Copyright 2006 Andres Riancho

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


class Configurable(object):
    """
    This is mostly "an interface", this "interface" states that all
    classes that implement it, should implement the following methods:
        1. set_options( options_list )
        2. get_options()

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def set_options(self, options_list):
        """
        Sets the Options given on the options_list to self. The options
        are the result of a user entering some data on a window that
        was constructed using the XML Options that was retrieved from
        the plugin using get_options()

        This method MUST be implemented on every configurable object.

        :return: No value is returned.
        """
        raise NotImplementedError('Configurable object is not implementing '
                                  'required method set_options')

    def get_options(self):
        """
        This method returns an OptionList containing the options
        objects that the configurable object has. Using this option
        list the framework will build a window, a menu, or some
        other input method to retrieve the info from the user.

        This method MUST be implemented on every plugin.

        :return: OptionList.
        """
        raise NotImplementedError('Configurable object is not implementing '
                                  'required method get_options')

    def get_name(self):
        return type(self).__name__

    def get_type(self):
        return 'configurable'
