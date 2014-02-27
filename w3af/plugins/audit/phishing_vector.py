"""
phishing_vector.py

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
from __future__ import with_statement

from lxml import etree

import w3af.core.data.constants.severity as severity

from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.kb.vuln import Vuln


class phishing_vector(AuditPlugin):
    """
    Find phishing vectors.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        AuditPlugin.__init__(self)

        # Some internal vars
        self._tag_xpath = etree.XPath('//iframe | //frame')

        # I test this with different URL handlers because the developer may have
        # blacklisted http:// and https:// but missed ftp://.
        #
        # I also use hTtp instead of http because I want to evade some (stupid)
        # case sensitive filters
        self._test_urls = ('hTtp://w3af.org/', 'htTps://w3af.org/',
                           'fTp://w3af.org/')

    def audit(self, freq, orig_response):
        """
        Find those phishing vectors!

        :param freq: A FuzzableRequest
        """
        mutants = create_mutants(freq, self._test_urls)

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result)

    def _analyze_result(self, mutant, response):
        """
        Analyze results of the _send_mutant method.
        """
        if self._has_bug(mutant):
            return
        
        dom = response.get_dom()

        if response.is_text_or_html() and dom is not None:

            elem_list = self._tag_xpath(dom)

            for element in elem_list:

                if 'src' not in element.attrib:
                    return []

                src_attr = element.attrib['src']

                for url in self._test_urls:
                    if src_attr.startswith(url):
                        # Vuln vuln!
                        desc = 'A phishing vector was found at: %s'
                        desc = desc % mutant.found_at()
                        
                        v = Vuln.from_mutant('Phishing vector', desc,
                                             severity.LOW, response.id,
                                             self.get_name(), mutant)
                        
                        v.add_to_highlight(src_attr)
                        self.kb_append_uniq(self, 'phishing_vector', v)


    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugins finds phishing vectors in web applications, for example,
        a bug of this type is found if I request the URL
        "http://site.tld/asd.asp?info=http://attacker.tld" and in the response
        HTML the web application sends:
            ...
            <iframe src="http://attacker.tld">
            ....
        """
