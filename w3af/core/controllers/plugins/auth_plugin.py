"""
AuthPlugin.py

Copyright 2011 Andres Riancho

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
from w3af.core.controllers.plugins.plugin import Plugin


class AuthPlugin(Plugin):
    """
    This is the base class for auth plugins, all auth plugins should inherit
    from it and implement the following methods:
        1. login(...)
        2. logout(...)
        2. is_logged(...)

    :author: Dmitriy V. Simonov ( dsimonov@yandex-team.com )
    """

    def __init__(self):
        Plugin.__init__(self)
        self._uri_opener = None

    def login(self):
        """
        Login user into web application.

        It is called in the begging of w3afCore::_discover_and_bruteforce() method
        if current user session is not valid.

        """
        raise NotImplementedError(
            'Plugin is not implementing required method login')

    def logout(self):
        """
        Logout user from web application.

        TODO: need to add calling of this method to w3afCore::_end()

        """
        raise NotImplementedError(
            'Plugin is not implementing required method logout')

    def is_logged(self):
        """
        Check if current session is still valid.

        It is called in the begging of w3afCore::_discover_and_bruteforce() method.
        """
        raise NotImplementedError(
            'Plugin is not implementing required method isLogged')

    def get_type(self):
        return 'auth'
