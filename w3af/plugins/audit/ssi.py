"""
ssi.py

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

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.fuzzer.utils import rand_alpha
from w3af.core.data.db.disk_dict import DiskDict
from w3af.core.data.db.disk_list import DiskList
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.esmre.multi_in import multi_in
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.controllers.exceptions import NoSuchTableException


class ssi(AuditPlugin):
    """
    Find server side inclusion vulnerabilities.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        AuditPlugin.__init__(self)

        # Internal variables
        self._expected_res_mutant = DiskDict(table_prefix='ssi')
        self._freq_list = DiskList(table_prefix='ssi')
        self._end_was_called = False
        
        re_str = '<!--#exec cmd="echo -n (.*?);echo -n (.*?)" -->'
        self._extract_results_re = re.compile(re_str)

    def audit(self, freq, orig_response):
        """
        Tests an URL for server side inclusion vulnerabilities.

        :param freq: A FuzzableRequest
        """
        # Create the mutants to send right now,
        ssi_strings = self._get_ssi_strings()
        mutants = create_mutants(freq, ssi_strings, orig_resp=orig_response)

        # Used in end() to detect "persistent SSI"
        for mut in mutants:
            token_value = mut.get_token_value()
            expected_result = self._extract_result_from_payload(token_value)
            try:
                self._expected_res_mutant[expected_result] = mut
            except NoSuchTableException, nste:
                self._handle_no_such_table(freq, orig_response, nste)

        self._freq_list.append(freq)
        # End of persistent SSI setup

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result)

    def _handle_no_such_table(self, request, response, nste):
        """
        I had a lot of issues trying to reproduce [0], so this code is just
        a helper for me to identify the root cause.

        [0] https://github.com/andresriancho/w3af/issues/10849

        :param nste: The original exception
        :param request: The comment we're analyzing
        :param response: The HTTP response
        :return: None, an exception with more information is re-raised
        """
        msg = ('A NoSuchTableException was raised by the DBMS. This issue is'
               ' related with #10849 , but since I was unable to reproduce'
               ' it, extra debug information is added to the exception:'
               '\n'
               '\n - Audit plugin end() was called: %s'
               '\n - Response ID is: %s'
               '\n - HTTP request URL: %s'
               '\n - Original exception: "%s"'
               '\n\n'
               'https://github.com/andresriancho/w3af/issues/10849\n')
        args = (self._end_was_called,
                response.get_id(),
                request.get_url(),
                nste)
        raise NoSuchTableException(msg % args)

    def _get_ssi_strings(self):
        """
        This method returns a list of server sides to try to include.

        :return: A string, see above.
        """
        yield '<!--#exec cmd="echo -n %s;echo -n %s" -->' % (rand_alpha(5),
                                                             rand_alpha(5))

        # TODO: Add mod_perl ssi injection support
        # http://www.sens.buffalo.edu/services/webhosting/advanced/perlssi.shtml
        #yield <!--#perl sub="sub {print qq/mod_perl is working!/;}" -->

    def _extract_result_from_payload(self, payload):
        """
        Extract the expected result from the payload we're sending.
        """
        match = self._extract_results_re.search(payload)
        return match.group(1) + match.group(2)

    def _analyze_result(self, mutant, response):
        """
        Analyze the result of the previously sent request.
        :return: None, save the vuln to the kb.
        """
        if self._has_no_bug(mutant):
            e_res = self._extract_result_from_payload(mutant.get_token_value())
            if e_res in response and not e_res in mutant.get_original_response_body():
                
                desc = 'Server side include (SSI) was found at: %s'
                desc = desc % mutant.found_at()
                
                v = Vuln.from_mutant('Server side include vulnerability', desc,
                                     severity.HIGH, response.id,
                                     self.get_name(), mutant)

                v.add_to_highlight(e_res)
                self.kb_append_uniq(self, 'ssi', v)

    def end(self):
        """
        This method is called when the plugin wont be used anymore and is used
        to find persistent SSI vulnerabilities.

        Example where a persistent SSI can be found:

        Say you have a "guest book" (a CGI application that allows visitors
        to leave messages for everyone to see) on a server that has SSI
        enabled. Most such guest books around the Net actually allow visitors
        to enter HTML code as part of their comments. Now, what happens if a
        malicious visitor decides to do some damage by entering the following:

        <!--#exec cmd="ls" -->

        If the guest book CGI program was designed carefully, to strip SSI
        commands from the input, then there is no problem. But, if it was not,
        there exists the potential for a major headache!

        For a working example please see moth VM.
        """
        multi_in_inst = multi_in(self._expected_res_mutant.keys())

        def filtered_freq_generator(freq_list):
            already_tested = ScalableBloomFilter()

            for freq in freq_list:
                if freq not in already_tested:
                    already_tested.add(freq)
                    yield freq

        def analyze_persistent(freq, response):

            for matched_expected_result in multi_in_inst.query(response.get_body()):
                # We found one of the expected results, now we search the
                # self._persistent_data to find which of the mutants sent it
                # and create the vulnerability
                mutant = self._expected_res_mutant[matched_expected_result]
                
                desc = ('Server side include (SSI) was found at: %s'
                        ' The result of that injection is shown by browsing'
                        ' to "%s".')
                desc %= (mutant.found_at(), freq.get_url())
                
                v = Vuln.from_mutant('Persistent server side include vulnerability',
                                     desc, severity.HIGH, response.id,
                                     self.get_name(), mutant)
                
                v.add_to_highlight(matched_expected_result)
                self.kb_append(self, 'ssi', v)

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      filtered_freq_generator(self._freq_list),
                                      analyze_persistent,
                                      cache=False)

        self._end_was_called = True
        self._expected_res_mutant.cleanup()
        self._freq_list.cleanup()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds server side include (SSI) vulnerabilities.
        """
