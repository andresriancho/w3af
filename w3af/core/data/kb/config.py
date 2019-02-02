"""
config.py

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


class Config(dict):
    """
    This class saves config parameters sent by the user.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def save(self, variable_name, value):
        """
        This method saves the variable_name value to a dict.
        """
        self[variable_name] = value

    def cleanup(self):
        """
        Cleanup internal data.
        """
        self.clear()


cf = Config()
