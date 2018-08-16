"""
grep_plugin.py

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
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.plugin import Plugin
from w3af.core.controllers.exceptions import FourOhFourDetectionException


class GrepPlugin(Plugin):
    """
    This is the base class for grep plugins, all grep plugins should
    inherit from it and implement the following method:
        1. grep(request, response)

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        super(GrepPlugin, self).__init__()

    def grep_wrapper(self, fuzzable_request, response):
        """
        This method tries to find patterns on responses.

        This method CAN be implemented on a plugin, but its better to
        do your searches in grep().

        :param fuzzable_request: This is the fuzzable request object that
                                 generated the current response being analyzed.
        :param response: This is the HTTPResponse object to test.
        :return: If something is found it must be reported to the output
                 manager and the KB.
        """
        # Take a look at should_grep in grep.py to understand other
        # filters which are applied before analyzing a response.
        try:
            self.grep(fuzzable_request, response)
        except FourOhFourDetectionException, ffde:
            # We simply ignore any exceptions we find during the 404 detection
            # process. FYI: This doesn't break the xurllib error handling which
            # happens at lower layers.
            #
            # https://github.com/andresriancho/w3af/issues/8949
            om.out.debug('%s' % ffde)

    def grep(self, fuzzable_request, response):
        """
        Analyze the response.

        :param fuzzable_request: The request that was sent
        :param response: The HTTP response obj
        """
        raise NotImplementedError('Plugin "%s" must not implement required '
                                  'method grep' % self.__class__.__name__)

    def get_type(self):
        return 'grep'
