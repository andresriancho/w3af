"""
rosetta_flash.py

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
from __future__ import with_statement

import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.kb.vuln import Vuln


class rosetta_flash(AuditPlugin):
    """
    Find Rosetta Flash vulnerabilities in JSONP endpoints
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    FLASH = ('CWSA7000hCD0Up0IZUnnnnnnnnnnnnnnnnnnnUU5nnnnnn3SUUnUUU7CiudIbE'
             'AtWGDtGDGwwwDDGDG0Gt0GDGwtGDG0sDttwwwDG33w0sDDt03G33333sDfBDIH'
             'TOHHoKHBhHZLxHHHrlbhHHtHRHXXHHHdHDuYAENjmENDaqfvjmENyDjmENJYYf'
             'mLzMENYQfaFQENYnfVNx1D0Up0IZUnnnnnnnnnnnnnnnnnnnUU5nnnnnn3SUUn'
             'UUU7CiudIbEAtwwwEDG3w0sG0stDDGtw0GDDwwwt3wt333333w03333gFPaEIQ'
             'SNvTnmAqICTcsacSCtiUAcYVsSyUcliUAcYVIkSICMAULiUAcYVq9D0Up0IZUn'
             'nnnnnnnnnnnnnnnnnnUU5nnnnnn3SUUnUUU7CiudIbEAtwwuG333swG033GDtp'
             'DtDtDGDD33333s03333sdFPOwWgotOOOOOOOwodFhfhFtFLFlHLTXXTXxT8D0U'
             'p0IZUnnnnnnnnnnnnnnnnnnnUU5nnnnnn3SUUnUUU7kiudIbEAt33swwEGDDtD'
             'G0GGDDwwwDt0wDGwwGG0sDDt033333GDt333swwv3sFPDtdtthLtDdthTthxth'
             'XXHHHHhHHHHHHhHXhHHHHXhXhXHXhHhiOUOsxCxHwWhsXKTgtSXhsDCDHshghS'
             'LhmHHhDXHhEOUoZQHHshghoeXehMdXwSlhsXkhehMdhwSXhXmHH5D0Up0IZUnn'
             'nnnnnnnnnnnnnnnnnUU5nnnnnn3SUUnUUUwGNqdIbe133333333333333333sU'
             'Uef03gfzA8880HUAH')

    def audit(self, freq, orig_response, debugging_id):
        """
        Tests a URL for rosetta flash vulnerabilities

        https://miki.it/blog/2014/7/8/abusing-jsonp-with-rosetta-flash/
        http://quaxio.com/jsonp_handcrafted_flash_files/
        https://molnarg.github.io/ascii-flash/#/24

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        content_type, _ = orig_response.get_headers().iget('Content-Type')

        if not content_type:
            return

        # Only check JSONP endpoints, other "reflections" like XSS are checked
        # in xss.py , have different severity, exploits, etc.
        if 'javascript' not in content_type or 'text/plain' not in content_type:
            return

        # Note that we're only creating QS mutants, since that's a requirement
        # to be able to "host" the reflected Flash in the vulnerable site
        mutants = create_mutants(freq, [self.FLASH], orig_resp=orig_response,
                                 mutant_tuple=[QSMutant])

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result,
                                      debugging_id=debugging_id)

    def _analyze_result(self, mutant, response):
        """
        Analyze results of the _send_mutant method, in order for a Rosetta Flash
        vulnerability to be present we need to have the FLASH attribute
        reflected at the beginning of the response body
        """
        if self._has_bug(mutant):
            return

        if not response.get_body().startswith(self.FLASH):
            return

        desc = 'Rosetta flash vulnerability found in JSONP endpoint at: %s'
        desc %= mutant.found_at()

        v = Vuln.from_mutant('Rosetta Flash', desc,
                             severity.LOW, response.id,
                             self.get_name(), mutant)
        v.add_to_highlight(self.FLASH)
        self.kb_append_uniq(self, 'rosetta_flash', v)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds JSONP endpoints which are vulnerable to Rosetta Flash.
        """

