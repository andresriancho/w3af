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
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om

from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.quick_match.multi_in import MultiIn
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.fuzzer.utils import rand_number
from w3af.core.data.db.disk_dict import DiskDict
from w3af.core.data.kb.vuln import Vuln


class ssi(AuditPlugin):
    """
    Find server side inclusion vulnerabilities.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        AuditPlugin.__init__(self)

        # Internal variables
        self._persistent_multi_in = None
        self._expected_mutant_dict = DiskDict(table_prefix='ssi')
        self._extract_expected_re = re.compile('[1-9]{5}')

    def audit(self, freq, orig_response, debugging_id):
        """
        Tests an URL for server side inclusion vulnerabilities.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        ssi_strings = self._get_ssi_strings()
        mutants = create_mutants(freq, ssi_strings, orig_resp=orig_response)

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result,
                                      debugging_id=debugging_id)

    def _get_ssi_strings(self):
        """
        This method returns a list of server sides to try to include.

        :return: A string, see above.
        """
        # Generic
        yield '<!--#exec cmd="echo -n %s;echo -n %s" -->' % get_seeds()

        # Perl SSI
        yield ('<!--#set var="SEED_A" value="%s" -->'
               '<!--#echo var="SEED_A" -->'
               '<!--#set var="SEED_B" value="%s" -->'
               '<!--#echo var="SEED_B" -->' % get_seeds())

        # Smarty
        # http://www.smarty.net/docsv2/en/language.function.math.tpl
        yield '{math equation="x * y" x=%s y=%s}' % get_seeds()

        # Mako
        # http://docs.makotemplates.org/en/latest/syntax.html
        yield '${%s * %s}' % get_seeds()

        # Jinja2 and Twig
        # http://jinja.pocoo.org/docs/dev/templates/#math
        # http://twig.sensiolabs.org/doc/templates.html
        yield '{{%s * %s}}' % get_seeds()

        # Generic
        yield '{%s * %s}' % get_seeds()

    def _get_expected_results(self, mutant):
        """
        Extracts the potential results from the mutant payload and returns them
        in a list.
        """
        sent_payload = mutant.get_token_payload()
        seed_numbers = self._extract_expected_re.findall(sent_payload)

        seed_a = int(seed_numbers[0])
        seed_b = int(seed_numbers[1])

        return [str(seed_a * seed_b), '%s%s' % (seed_a, seed_b)]

    def _analyze_result(self, mutant, response):
        """
        Analyze the result of the previously sent request.
        :return: None, save the vuln to the kb.
        """
        # Store the mutants in order to be able to analyze the persistent case
        # later
        expected_results = self._get_expected_results(mutant)

        for expected_result in expected_results:
            self._expected_mutant_dict[expected_result] = mutant

        # Now we analyze the "reflected" case
        if self._has_bug(mutant):
            return

        for expected_result in expected_results:
            if expected_result not in response:
                continue

            if expected_result in mutant.get_original_response_body():
                continue

            desc = 'Server side include (SSI) was found at: %s'
            desc %= mutant.found_at()

            v = Vuln.from_mutant('Server side include vulnerability', desc,
                                 severity.HIGH, response.id,
                                 self.get_name(), mutant)

            v.add_to_highlight(expected_result)
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
        fuzzable_request_set = kb.kb.get_all_known_fuzzable_requests()

        debugging_id = rand_alnum(8)
        om.out.debug('Starting stored SSI search (did=%s)' % debugging_id)

        #
        # TODO
        #
        # After identifying the issue we have in these lines, I should change
        # this code to use:
        #
        #   len(self._expected_mutant_dict)
        #   self._expected_mutant_dict.iterkeys()
        #
        # Those two methods are faster and consume less memory than the things
        # I'm doing below now.
        #
        expected_strings = self._expected_mutant_dict.keys()
        args = (len(expected_strings), debugging_id)
        om.out.debug('About to create MultiIn with %s keys (did=%s)' % args)

        self._persistent_multi_in = MultiIn(expected_strings)
        om.out.debug('Created stored SSI MultiIn (did=%s)' % debugging_id)

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      fuzzable_request_set,
                                      self._analyze_persistent,
                                      cache=False,
                                      debugging_id=debugging_id)

        self._expected_mutant_dict.cleanup()

    def _analyze_persistent(self, freq, response):
        """
        Analyze the response of sending each fuzzable request found by the
        framework, trying to identify any locations where we might have injected
        a payload.

        :param freq: The fuzzable request
        :param response: The HTTP response
        :return: None, vulns are stored in KB
        """
        msg = 'Analyzing HTTP response %s to verify if SSI string is found'
        om.out.debug(msg % response.get_uri())

        for matched_expected_result in self._persistent_multi_in.query(response.get_body()):
            # We found one of the expected results, now we search the
            # self._expected_mutant_dict to find which of the mutants sent it
            # and create the vulnerability
            mutant = self._expected_mutant_dict[matched_expected_result]

            desc = ('Server side include (SSI) was found at: %s'
                    ' The result of that injection is shown by browsing'
                    ' to "%s".')
            desc %= (mutant.found_at(), freq.get_url())

            v = Vuln.from_mutant('Persistent server side include vulnerability',
                                 desc, severity.HIGH, response.id,
                                 self.get_name(), mutant)

            v.add_to_highlight(matched_expected_result)
            self.kb_append(self, 'ssi', v)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds server side include (SSI) vulnerabilities, also
        recently renamed to Server-Side Template Injection vulnerabilities.

        http://blog.portswigger.net/2015/08/server-side-template-injection.html
        """


def get_seeds():
    """
    :return: A couple of random numbers which will be used to make the payloads
             unique. Please note that I'm excluding the zeroes in order to avoid
             some bugs where leading zeroes are truncated.
    """
    return (rand_number(5, exclude_numbers=(0,)),
            rand_number(5, exclude_numbers=(0,)))
