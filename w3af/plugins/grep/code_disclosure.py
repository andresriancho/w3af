"""
code_disclosure.py

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

from w3af.core.data.kb.vuln import Vuln
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.misc.contains_source_code import contains_source_code


class code_disclosure(GrepPlugin):
    """
    Grep every page for code disclosure vulnerabilities.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        GrepPlugin.__init__(self)

        # Internal variables
        self._report_404_match = True

    def grep(self, request, response):
        """
        Plugin entry point, search for the code disclosures.

        Unit tests are available at plugins/grep/tests.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        if not response.is_text_or_html():
            return

        response_is_404 = is_404(response)

        # This is a performance improvement to prevent the plugin from
        # applying contains_source_code to a 404 response that will be
        # discarded even if it matches
        if response_is_404 and not self._report_404_match:
            return

        match, lang = contains_source_code(response)

        if not match:
            return

        # Only report 404 findings once
        if response_is_404 and self._report_404_match:
            self._report_404_match = False

            desc = (u'The URL: "%s" has a %s code disclosure'
                    u' vulnerability in the customized 404 script.')
            name = u'Code disclosure vulnerability in 404 page'
        else:
            desc = u'The URL: "%s" has a %s code disclosure vulnerability.'
            name = u'Code disclosure vulnerability'

        # Report the vulnerability
        desc %= (response.get_url(), ' or '.join(list(lang)))

        v = Vuln(name, desc, severity.LOW, response.id, self.get_name())
        v.set_url(response.get_url())
        v.add_to_highlight(match.group())
        
        self.kb_append_uniq(self, 'code_disclosure', v, 'URL')

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page in order to find code disclosures.
        Basically it greps for '<?.*?>' and '<%.*%>' using the re module and
        reports findings.

        Code disclosures are usually generated due to web server
        misconfigurations, or weird web application "features".
        """
