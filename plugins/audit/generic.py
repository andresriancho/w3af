'''
generic.py

Copyright 2007 Andres Riancho

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
import copy

import core.data.kb.knowledge_base as kb
import core.data.constants.severity as severity

from core.data.options.opt_factory import opt_factory
from core.data.options.option_list import OptionList
from core.data.fuzzer.fuzzer import create_mutants
from core.data.fuzzer.utils import rand_number, rand_alnum
from core.controllers.plugins.audit_plugin import AuditPlugin
from core.controllers.misc.levenshtein import relative_distance
from core.data.kb.vuln import Vuln
from core.data.kb.info import Info


class generic(AuditPlugin):
    '''
    Find all kind of bugs without using a fixed database of errors.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        AuditPlugin.__init__(self)

        #   Internal variables
        self._already_reported = []

        #   User configured variables
        self._diff_ratio = 0.30

    def audit(self, freq):
        '''
        Find all kind of bugs without using a fixed database of errors.

        @param freq: A FuzzableRequest
        '''
        # First, get the original response and create the mutants
        orig_resp = self._uri_opener.send_mutant(freq)
        mutants = create_mutants(freq, ['', ], orig_resp=orig_resp)

        for m in mutants:

            # First I check that the current modified parameter in the mutant
            # doesn't have an already reported vulnerability. I don't want to
            # report vulnerabilities more than once.
            if (m.get_url(), m.get_var()) in self._already_reported:
                continue

            # Now, we request the limit (something that doesn't exist)
            # If http://localhost/a.php?b=1 ; then I should request b=12938795
            #                                                       (random number)
            # If http://localhost/a.php?b=abc ; then I should request b=hnv98yks
            #                                                         (random alnum)
            limit_response = self._get_limit_response(m)

            # Now I request something that could generate an error
            #     If http://localhost/a.php?b=1 ; then I should request b=d'kcz'gj'"**5*(((*)
            #     If http://localhost/a.php?b=abc ; then I should request b=d'kcz'gj'"**5*(((*)
            #
            # I also try to trigger errors by sending empty strings
            #     If http://localhost/a.php?b=1 ; then I should request b=
            #     If http://localhost/a.php?b=abc ; then I should request b=
            for error_string in self._get_error_strings():

                if self._has_no_bug(m):

                    m.set_mod_value(error_string)
                    error_response = self._uri_opener.send_mutant(m)

                    # Now I compare all responses
                    self._analyze_responses(
                        orig_resp, limit_response, error_response, m)

    def _get_error_strings(self):
        '''
        @return: A list of strings that could generate errors. Please note that
                 an empty string is something that, in most cases, is not tested.
                 Although, I have found that it could trigger some errors.
        '''
        return ['d\'kc"z\'gj\'\"**5*(((;-*`)', '']

    def _analyze_responses(self, orig_resp, limit_response, error_response, mutant):
        '''
        Analyze responses; if error_response doesn't look like orig_resp nor
        limit_response, then we have a vuln.

        @return: None
        '''
        original_to_error = relative_distance(
            orig_resp.get_body(), error_response.get_body())
        limit_to_error = relative_distance(
            limit_response.get_body(), error_response.get_body())
        original_to_limit = relative_distance(
            limit_response.get_body(), orig_resp.get_body())

        ratio = self._diff_ratio + (1 - original_to_limit)

        #om.out.debug('original_to_error: ' +  str(original_to_error) )
        #om.out.debug('limit_to_error: ' +  str(limit_to_error) )
        #om.out.debug('original_to_limit: ' +  str(original_to_limit) )
        #om.out.debug('ratio: ' +  str(ratio) )

        if original_to_error < ratio and limit_to_error < ratio:
            # Maybe the limit I requested wasn't really a non-existant one
            # (and the error page really found the limit),
            # let's request a new limit (one that hopefully doesn't exist)
            # in order to remove some false positives
            limit_response2 = self._get_limit_response(mutant)

            id_list = [orig_resp.id, limit_response.id, error_response.id]

            if relative_distance(limit_response2.get_body(), limit_response.get_body()) > \
                    1 - self._diff_ratio:
                # The two limits are "equal"; It's safe to suppose that we have found the
                # limit here and that the error string really produced an error
                desc = 'An unidentified vulnerability was found at: %s'
                desc = desc % mutant.found_at()
                
                v = Vuln.from_mutant('Unidentified vulnerability', desc,
                                     severity.MEDIUM, id_list, self.get_name(),
                                     mutant)

                self.kb_append_uniq(self, 'generic', v)
                self._already_reported.append((mutant.get_url(),
                                               mutant.get_var()))
            else:
                # *maybe* and just *maybe* this is a vulnerability
                desc = '[Manual verification required] A potential' \
                       'vulnerability was found at: %s'
                desc = desc % mutant.found_at()
                
                i = Info.from_mutant('Potential unidentified vulnerability',
                                     desc, id_list, self.get_name(), mutant)
                
                self.kb_append_uniq(self, 'generic', i)
                
                self._already_reported.append((mutant.get_url(),
                                               mutant.get_var()))

    def _get_limit_response(self, m):
        '''
        We request the limit (something that doesn't exist)
            - If http://localhost/a.php?b=1 ; then I should request b=12938795
                                                                 (random number)
            - If http://localhost/a.php?b=abc ; then I should request b=hnv98yks
                                                                    (random alnum)

        @return: The limit response object
        '''
        # Copy the dc, needed to make a good vuln report
        dc = copy.deepcopy(m.get_dc())

        if m.get_original_value().isdigit():
            m.set_mod_value(rand_number(length=8))
        else:
            m.set_mod_value(rand_alnum(length=8))
        limit_response = self._uri_opener.send_mutant(m)

        # restore the dc
        m.set_dc(dc)
        return limit_response

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        vulnsAndInfos = kb.kb.get_all_vulns()
        vulnsAndInfos.extend(kb.kb.get_all_infos())
        self.print_uniq(vulnsAndInfos, 'VAR')

    def get_options(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = OptionList()

        d = 'If two strings have a diff ratio less than diffRatio, then they are '
        d += '*really* different'
        o = opt_factory('diffRatio', self._diff_ratio, d, 'float')
        ol.add(o)

        return ol

    def set_options(self, options_list):
        '''
        This method sets all the options that are configured using the user interface
        generated by the framework using the result of get_options().

        @param OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        '''
        self._diff_ratio = options_list['diffRatio'].get_value()

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds all kind of bugs without using a fixed database of
        errors. This is a new kind of methodology that solves the main problem
        of most web application security scanners.
        '''
