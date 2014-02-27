"""
click_jacking.py

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
import w3af.core.data.constants.severity as severity

from w3af.core.data.db.disk_list import DiskList
from w3af.core.data.kb.vuln import Vuln
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin


class click_jacking(GrepPlugin):
    """
    Grep every page for X-Frame-Options header.

    :author: Taras (oxdef@oxdef.info)
    """

    def __init__(self):
        GrepPlugin.__init__(self)

        self._total_count = 0
        self._vuln_count = 0
        self._vulns = DiskList()
        self._ids = DiskList()

    def grep(self, request, response):
        """
        TODO: need to check here for auth cookie?!
        """
        if not response.is_text_or_html():
            return

        self._total_count += 1

        headers = response.get_lower_case_headers()
        x_frame_options = headers.get('x-frame-options', '')

        if not x_frame_options.lower() in ('deny', 'sameorigin'):
            self._vuln_count += 1
            if response.get_url() not in self._vulns:
                self._vulns.append(response.get_url())
                self._ids.append(response.id)

    def end(self):
        # If all URLs implement protection, don't report anything.
        if not self._vuln_count:
            return

        response_ids = [_id for _id in self._ids]
        
        # If none of the URLs implement protection, simply report
        # ONE vulnerability that says that.
        if self._total_count == self._vuln_count:
            desc = 'The whole target has no protection (X-Frame-Options'\
                  ' header) against Click-Jacking attacks'
        # If most of the URLs implement the protection but some
        # don't, report ONE vulnerability saying: "Most are protected,
        # but x, y are not.
        if self._total_count > self._vuln_count:
            desc = 'Some URLs have no protection (X-Frame-Options header) '\
                  'against Click-Jacking attacks. Among them:\n '\
                  ' '.join([str(url) + '\n' for url in self._vulns])

        v = Vuln('Click-Jacking vulnerability', desc,
                 severity.MEDIUM, response_ids, self.get_name())
        
        self.kb_append(self, 'click_jacking', v)
        
        self._vulns.cleanup()
        self._ids.cleanup()

    def get_long_desc(self):
        return """
        This plugin greps every page for X-Frame-Options header and so
        for possible ClickJacking attack against URL.

        Additional information: https://www.owasp.org/index.php/Clickjacking
        """
