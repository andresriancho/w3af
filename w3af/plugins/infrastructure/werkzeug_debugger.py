"""
werkzeug_debugger.py

Copyright 2015 Andres Riancho

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
from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.data.constants.severity import HIGH
from w3af.core.data.kb.vuln import Vuln


class werkzeug_debugger(InfrastructurePlugin):
    """
    Detect if Werkzeug's debugger is enabled.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    TEST_URL = '/?__debugger__=yes&cmd=resource&f=debugger.js'
    REQUIRED_STRINGS = ('CONSOLE_MODE', 'openShell', 'console.png')

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        url = fuzzable_request.get_url().url_join(self.TEST_URL)
        response = self._uri_opener.GET(url, cache=False, grep=False)

        # All strings need to be there
        for req_string in self.REQUIRED_STRINGS:
            if req_string not in response.get_body():
                return

        desc = ("Werkzeug's debugger allows unauthenticated attackers to"
                " execute arbitrary Python code.")

        v = Vuln('Werkzeug debugger enabled', desc, HIGH, response.id,
                 self.get_name())
        v.set_url(response.get_url())

        self.kb_append_uniq(self, 'werkzeug_debugger', v)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Werkzeug's debugger allows unauthenticated attackers to execute
        arbitrary Python code. This plugin detects if the target Web application
        has the debugger enabled.

        http://colin.keigher.ca/2014/12/remote-code-execution-on-misconfigured.html
        """