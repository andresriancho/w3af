"""
xpath.py

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

import w3af.core.controllers.output_manager as om

import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.quick_match.multi_in import MultiIn
from w3af.core.data.kb.vuln import Vuln


class xpath(AuditPlugin):
    """
    Find XPATH injection vulnerabilities.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    XPATH_PATTERNS = (
        'System.Xml.XPath.XPathException:',
        'MS.Internal.Xml.',
        'Unknown error in XPath',
        'org.apache.xpath.XPath',
        'A closing bracket expected in',
        'An operand in Union Expression does not produce a node-set',
        'Cannot convert expression to a number',
        'Document Axis does not allow any context Location Steps',
        'Empty Path Expression',
        'DOMXPath::'
        'Empty Relative Location Path',
        'Empty Union Expression',
        "Expected ')' in",
        'Expected node test or name specification after axis operator',
        'Incompatible XPath key',
        'Incorrect Variable Binding',
        'libxml2 library function failed',
        'libxml2',
        'Invalid predicate',
        'Invalid expression',
        'xmlsec library function',
        'xmlsec',
        "error '80004005'",
        "A document must contain exactly one root element.",
        '<font face="Arial" size=2>Expression must evaluate to a node-set.',
        "Expected token ']'",
        "<p>msxml4.dll</font>",
        "<p>msxml3.dll</font>",

        # Put this here cause i did not know if it was a sql injection
        # This error appears when you put wierd chars in a lotus notes document
        # search ( nsf files ).
        '4005 Notes error: Query is not understandable',
    )
    _multi_in = MultiIn(XPATH_PATTERNS)

    XPATH_TEST_PAYLOADS = [
        "d'z\"0",
        # http://www.owasp.org/index.php/Testing_for_XML_Injection
        "<!--"
    ]

    def audit(self, freq, orig_response, debugging_id):
        """
        Tests an URL for xpath injection vulnerabilities.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        mutants = create_mutants(freq, self.XPATH_TEST_PAYLOADS,
                                 orig_resp=orig_response)

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result,
                                      debugging_id=debugging_id)

    def _analyze_result(self, mutant, response):
        """
        Analyze results of the _send_mutant method.
        """
        #
        #   I will only report the vulnerability once.
        #
        if self._has_bug(mutant):
            return

        xpath_error_list = self._find_xpath_error(response)
        for xpath_error in xpath_error_list:
            if xpath_error not in mutant.get_original_response_body():

                desc = 'XPATH injection was found at: %s' % mutant.found_at()

                v = Vuln.from_mutant('XPATH injection vulnerability', desc,
                                     severity.MEDIUM, response.id,
                                     self.get_name(), mutant)

                v.add_to_highlight(xpath_error)
                self.kb_append_uniq(self, 'xpath', v)
                break

    def _find_xpath_error(self, response):
        """
        This method searches for xpath errors in html's.

        :param response: The HTTP response object
        :return: A list of errors found on the page
        """
        res = []
        for xpath_error_match in self._multi_in.query(response.body):
            msg = 'Found XPATH injection. The error showed by the web'\
                  ' application is (only a fragment is shown): "%s".'\
                  ' The error was found on response with id %s.'
            om.out.information(msg % (xpath_error_match, response.id))
            res.append(xpath_error_match)
        return res

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before
                 the current one.
        """
        return ['grep.error_500']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds XPATH injections.

        To find this vulnerabilities the plugin sends the string "d'z'0" to
        every injection point, and searches the response for XPATH errors.
        """
