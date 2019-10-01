"""
infrastructure_plugin.py

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
from w3af.core.controllers.misc.safe_deepcopy import safe_deepcopy
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.exceptions import FourOhFourDetectionException

import w3af.core.controllers.output_manager as om


class InfrastructurePlugin(Plugin):
    """
    This is the base class for infrastructure plugins, all infrastructure
    plugins should inherit from it and implement the following methods:
        1. discover(...)

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def discover_wrapper(self, fuzzable_request, debugging_id):
        """
        Wrapper around the discover method to perform generic tasks such
        as cloning the fuzzable request.

        :param fuzzable_request: The target to use for infrastructure plugins.
        :param debugging_id: A unique identifier for this call to discover()
        """
        # I copy the fuzzable request, to avoid cross plugin contamination
        # in other words, if one plugin modified the fuzzable request object
        # INSIDE that plugin, I don't want the next plugin to suffer from that
        fuzzable_request_copy = safe_deepcopy(fuzzable_request)

        try:
            return self.discover(fuzzable_request_copy, debugging_id)
        except FourOhFourDetectionException, ffde:
            # We simply ignore any exceptions we find during the 404 detection
            # process. FYI: This doesn't break the xurllib error handling which
            # happens at lower layers.
            #
            # https://github.com/andresriancho/w3af/issues/8949
            om.out.debug('%s' % ffde)

    def discover(self, fuzzable_request, debugging_id):
        """
        This method MUST be implemented on every plugin.

        :param fuzzable_request: The target to use for infrastructure plugins.
        :param debugging_id: A unique identifier for this call to discover()
        :return: None. These plugins should store information in the KB. Results
                 from this method will be ignored by the core.
        """
        msg = 'Plugin is not implementing required method discover'
        raise BaseFrameworkException(msg)

    def get_type(self):
        return 'infrastructure'
