"""
InfrastructurePlugin.py

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
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.request.factory import create_fuzzable_requests


class InfrastructurePlugin(Plugin):
    """
    This is the base class for infrastructure plugins, all infrastructure plugins
    should inherit from it and implement the following methods:
        1. discover(...)

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        Plugin.__init__(self)

    def discover_wrapper(self, fuzzable_request):
        """
        Wrapper around the discover method in order to perform some generic tasks.
        """
        # I copy the fuzzable request, to avoid cross plugin contamination
        # in other words, if one plugin modified the fuzzable request object
        # INSIDE that plugin, I don't want the next plugin to suffer from that
        fuzzable_request_copy = fuzzable_request.copy()
        return self.discover(fuzzable_request_copy)

    def discover(self, fuzzable_request):
        """
        This method MUST be implemented on every plugin.

        :param fuzzable_request: The target to use for infrastructure plugins.
        :return: None. These plugins should store information in the KB. Results
                 from this method will be ignored by the core.
        """
        raise BaseFrameworkException(
            'Plugin is not implementing required method discover')

    def _create_fuzzable_requests(self, HTTPResponse, request=None, add_self=True):
        return create_fuzzable_requests(HTTPResponse, request, add_self)

    def get_type(self):
        return 'infrastructure'
