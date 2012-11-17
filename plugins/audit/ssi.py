'''
ssi.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
import re

import core.controllers.output_manager as om
import core.data.constants.severity as severity
import core.data.kb.knowledge_base as kb
import core.data.kb.vuln as vuln

from core.controllers.plugins.audit_plugin import AuditPlugin
from core.data.fuzzer.fuzzer import create_mutants
from core.data.fuzzer.utils import rand_alpha
from core.data.db.temp_shelve import temp_shelve
from core.data.db.disk_list import disk_list
from core.data.esmre.multi_in import multi_in
from core.data.bloomfilter.scalable_bloom import ScalableBloomFilter


class ssi(AuditPlugin):
    '''
    Find server side inclusion vulnerabilities.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        AuditPlugin.__init__(self)

        # Internal variables
        self._expected_res_mutant = temp_shelve()
        self._freq_list = disk_list()

    def audit(self, freq):
        '''
        Tests an URL for server side inclusion vulnerabilities.

        @param freq: A FuzzableRequest
        '''
        orig_resp = self._uri_opener.send_mutant(freq)

        # Create the mutants to send right now,
        ssi_strings = self._get_ssi_strings()
        mutants = create_mutants(freq, ssi_strings, orig_resp=orig_resp)

        # Used in end() to detect "persistent SSI"
        for m in mutants:
            expected_result = self._extract_result_from_payload(
                m.get_mod_value())
            self._expected_res_mutant[expected_result] = m

        self._freq_list.append(freq)
        # End of persistent SSI setup

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result)

    def _get_ssi_strings(self):
        '''
        This method returns a list of server sides to try to include.

        @return: A string, see above.
        '''
        yield '<!--#exec cmd="echo -n %s;echo -n %s" -->' % (rand_alpha(5),
                                                             rand_alpha(5))

        # TODO: Add mod_perl ssi injection support
        # http://www.sens.buffalo.edu/services/webhosting/advanced/perlssi.shtml
        #yield <!--#perl sub="sub {print qq/If you see this, mod_perl is working!/;}" -->

    def _extract_result_from_payload(self, payload):
        '''
        Extract the expected result from the payload we're sending.
        '''
        mo = re.search(
            '<!--#exec cmd="echo -n (.*?);echo -n (.*?)" -->', payload)
        return mo.group(1) + mo.group(2)

    def _analyze_result(self, mutant, response):
        '''
        Analyze the result of the previously sent request.
        @return: None, save the vuln to the kb.
        '''
        if self._has_no_bug(mutant):
            e_res = self._extract_result_from_payload(mutant.get_mod_value())
            if e_res in response and not e_res in mutant.get_original_response_body():
                v = vuln.vuln(mutant)
                v.set_plugin_name(self.get_name())
                v.set_name('Server side include vulnerability')
                v.set_severity(severity.HIGH)
                v.set_desc('Server side include (SSI) was found at: ' +
                           mutant.found_at())
                v.set_id(response.id)
                v.addToHighlight(e_res)
                kb.kb.append_uniq(self, 'ssi', v)

    def end(self):
        '''
        This method is called when the plugin wont be used anymore and is used
        to find persistent SSI vulnerabilities.

        Example where a persistent SSI can be found:

        Say you have a "guestbook" (a CGI application that allows visitors
        to leave messages for everyone to see) on a server that has SSI
        enabled. Most such guestbooks around the Net actually allow visitors
        to enter HTML code as part of their comments. Now, what happens if a
        malicious visitor decides to do some damage by entering the following:

        <!--#exec cmd="ls" -->

        If the guestbook CGI program was designed carefully, to strip SSI
        commands from the input, then there is no problem. But, if it was not,
        there exists the potential for a major headache!

        For a working example please see moth VM.
        '''
        multi_in_inst = multi_in(self._expected_res_mutant.keys())

        def filtered_freq_generator(freq_list):
            already_tested = ScalableBloomFilter()

            for freq in freq_list:
                if freq not in already_tested:
                    already_tested.add(freq)
                    yield freq

        def analyze_persistent(freq, response):

            for matched_expected_result in multi_in_inst.query(response.getBody()):
                # We found one of the expected results, now we search the
                # self._persistent_data to find which of the mutants sent it
                # and create the vulnerability
                mutant = self._expected_res_mutant[matched_expected_result]
                v = vuln.vuln(mutant)
                v.set_plugin_name(self.get_name())
                v.set_name('Persistent server side include vulnerability')
                v.set_severity(severity.HIGH)
                msg = 'Server side include (SSI) was found at: ' + \
                    mutant.found_at()
                msg += ' The result of that injection is shown by'
                msg += ' browsing to "%s".' % freq.getURL()
                v.set_desc(msg)
                v.set_id(response.id)
                v.addToHighlight(matched_expected_result)
                kb.kb.append(self, 'ssi', v)

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      filtered_freq_generator(self._freq_list),
                                      analyze_persistent,
                                      cache=False)

        self.print_uniq(kb.kb.get('ssi', 'ssi'), 'VAR')

    def _find_file(self, response):
        '''
        This method finds out if the server side has been successfully included in
        the resulting HTML.

        @param response: The HTTP response object
        @return: A list of errors found on the page
        '''
        res = []
        for file_pattern_match in self._multi_in.query(response.body):
            msg = 'Found file pattern. The section where the file pattern is included is (only'
            msg += ' a fragment is shown): "' + file_pattern_match
            msg += '". The error was found on response with id ' + \
                str(response.id) + '.'
            om.out.information(msg)
            res.append(file_pattern_match)
        return res

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds server side include (SSI) vulnerabilities.
        '''
