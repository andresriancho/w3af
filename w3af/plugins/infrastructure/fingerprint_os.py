"""
fingerprint_os.py

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
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_equal
from w3af.core.data.kb.info import Info
from w3af.core.data.parsers.doc.url import URL


class fingerprint_os(InfrastructurePlugin):
    """
    Fingerprint the remote operating system using the HTTP protocol.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        self._exec = True

    def discover(self, fuzzable_request, debugging_id):
        """
        It calls the "main" and writes the results to the kb.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        if not self._exec:
            raise RunOnce()

        self._exec = not self._find_OS(fuzzable_request)

    def _find_OS(self, fuzzable_request):
        """
        Analyze responses and determine if remote web server runs on windows
        or *nix.

        @Return: None, the knowledge is saved in the knowledgeBase
        """
        freq_url = fuzzable_request.get_url()
        filename = freq_url.get_file_name()
        dirs = freq_url.get_directories()[:-1]  # Skipping "domain level" dir.

        if dirs and filename:

            last_url = dirs[-1]
            last_url = last_url.url_string

            windows_url = URL(last_url[0:-1] + '\\' + filename)
            windows_response = self._uri_opener.GET(windows_url)

            original_response = self._uri_opener.GET(freq_url)

            if fuzzy_equal(original_response.get_body(),
                                    windows_response.get_body(), 0.98):
                desc = 'Fingerprinted this host as a Microsoft Windows system.'
                os_str = 'windows'
            else:
                desc = 'Fingerprinted this host as a *nix system. Detection for'\
                       ' this operating system is weak, "if not windows then'\
                       ' linux".'
                os_str = 'unix'

            response_ids = [windows_response.id, original_response.id]
            i = Info('Operating system', desc, response_ids,
                     self.get_name())
            i.set_url(windows_response.get_url())
            
            kb.kb.raw_write(self, 'operating_system_str', os_str)
            kb.kb.append(self, 'operating_system', i)
            om.out.information(i.get_desc())
            return True

        return False

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin fingerprints the remote web server and tries to determine the
        Operating System family (Windows, Unix, etc.).

        The fingerprinting is (at this moment) really trivial, because it only
        uses one technique: windows path separator in the URL. For example, if the
        input URL is http://host.tld/abc/def.html then the plugin verifies if the
        response for that resource and the http://host.tld/abc\\def.html is the same;
        which indicates that the server is running Windows.
        """
