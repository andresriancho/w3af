"""
private_keys.py

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
import re

import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.vuln import Vuln


class private_keys(GrepPlugin):
    """
    Grep every page for private keys.

    :author: Yvonne Kim
    """
    def __init__(self):
        GrepPlugin.__init__(self)

        key_regex = '-----BEGIN RSA PRIVATE KEY-----\n[^-]+\n-----END RSA PRIVATE KEY-----'

        self._key_regex = re.compile(key_regex, re.M)


    def grep(self, request, response):
        """
        Plugin entry point, find the error pages and report them.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        if not response.is_text_or_html():
            return

        if not response.get_code() == 200:
            return

        clear_text_body = response.get_clear_text_body()

        if clear_text_body is None:
            return

        found_keys = self._find_keys(clear_text_body)

        for key in found_keys:
            desc = u'The URL: "%s" discloses the private key: "%s"'
            desc %= (response.get_url(), key)

            v = Vuln('private key disclosure', desc,
                     severity.LOW, response.id, self.get_name())

            v.set_url(response.get_url())
            v.add_to_highlight(key)

            self.kb_append_uniq(self, 'private_keys', v, 'URL')

    def _find_keys(self, body):
        """
        :return: A list of matching private keys
        """
        res = []

        match_list = self._key_regex.findall(body)
        
        for match in match_list:
            res.append(match)

        return res

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """

        return """
        This plugin scans responses for private keys.

        """
