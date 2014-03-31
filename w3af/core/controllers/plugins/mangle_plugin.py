"""
ManglePlugin.py

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
from w3af.core.controllers.plugins.plugin import Plugin


class ManglePlugin(Plugin):
    """
    This is the base class for mangle plugins, all mangle plugins should
    inherit from it and implement the following methods :
        1. mangle_request( request )
        2. mangle_response( request )
        3. set_options( OptionList )
        4. get_options()

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def get_type(self):
        return 'mangle'

    def __init__(self):
        Plugin.__init__(self)
        self._priority = 20

    def mangle_request(self, request):
        """
        This method mangles the request.

        This method MUST be implemented on every plugin.

        :param request: This is the request to mangle.
        :return: A mangled version of the request.
        """
        raise NotImplementedError

    def mangle_response(self, response):
        """
        This method mangles the response.

        This method MUST be implemented on every plugin.

        :param response: This is the response to mangle.
        :return: A mangled version of the response.
        """
        raise NotImplementedError

    def set_url_opener(self, foo):
        pass

    def __gt__(self, other):
        """
        This function is called when sorting mangle plugins.
        """
        if self.get_priority() > other.get_priority():
            return True
        else:
            return False

    def __lt__(self, other):
        """
        This function is called when sorting evasion plugins.
        """
        return not self.__gt__(other)

    def __eq__(self, other):
        """
        This function is called when sorting mangle plugins.
        """
        if self.get_priority() == other.get_priority():
            return True
        else:
            return False

    def get_priority(self):
        """
        This function is called when sorting mangle plugins.
        Each mangle plugin should implement this.

        :return: An integer specifying the priority. 100 is run first, 0 last.
        """
        return self._priority

    def _fix_content_len(self, response):
        """
        If the content-length header is present, calculate the new len and
        update the header.
        """
        cl = 'Content-Length'
        for i in response.get_headers():
            if i.lower() == 'content-length':
                cl = i
                break

        headers = response.get_headers()
        headers[cl] = str(len(response.get_body()))
        response.set_headers(headers)
        return response

