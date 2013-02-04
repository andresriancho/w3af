'''
redos.py

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

'''
from __future__ import with_statement

import core.controllers.output_manager as om

import core.data.constants.severity as severity
import core.data.kb.knowledge_base as kb

from core.controllers.plugins.audit_plugin import AuditPlugin
from core.data.fuzzer.fuzzer import create_mutants
from core.data.kb.vuln import Vuln
from core.data.kb.info import Info


class redos(AuditPlugin):
    '''
    Find ReDoS vulnerabilities.

    @author: Sebastien Duquette ( sebastien.duquette@gmail.com )
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    
    DELAY_PATTERNS = ['aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaX!',
                      'a@a.aaaaaaaaaaaaaaaaaaaaaaX!'
                      '1111111111111111111111111111111119!']
    
    def __init__(self):
        AuditPlugin.__init__(self)

        # Some internal variables
        # The wait time of the unmodified request
        self._original_wait_time = 0

        # The wait time of the first test I'm going to perform
        self._wait_time = 1

    def audit(self, freq, orig_response):
        '''
        Tests an URL for ReDoS vulnerabilities using time delays.

        @param freq: A FuzzableRequest
        '''
        #
        #   We know for a fact that PHP is NOT vulnerable to this attack
        #
        #   TODO: Add other frameworks that are not vulnerable!
        #
        for powered_by in kb.kb.get('server_header', 'powered_by_string'):
            if 'php' in powered_by.lower():
                return

        if 'php' in freq.get_url().get_extension().lower():
            return

        # Send the FuzzableRequest without any fuzzing, so we can measure the
        # response time of this script in order to compare it later
        self._original_wait_time = orig_response.get_wait_time()

        # Prepare the strings to create the mutants
        mutants = create_mutants(freq, self.DELAY_PATTERNS)

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_wait)

    def _analyze_wait(self, mutant, response):
        '''
        Analyze results of the _send_mutant method that was sent in the audit
        method.
        '''
        if self._has_bug(mutant, pname='preg_replace',
                         kb_varname='preg_replace'):
            return

        if response.get_wait_time() > (self._original_wait_time + self._wait_time):

            # This could be because of a ReDoS vuln, an error that generates a
            # delay in the response or simply a network delay; so I'll re-send
            # changing the length and see what happens.

            first_wait_time = response.get_wait_time()

            # Replace the old pattern with the new one:
            original_wait_param = mutant.get_mod_value()
            more_wait_param = original_wait_param.replace('X', 'XX')
            more_wait_param = more_wait_param.replace('9', '99')
            mutant.set_mod_value(more_wait_param)

            # send
            response = self._uri_opener.send_mutant(mutant)

            # compare the times
            if response.get_wait_time() > (first_wait_time * 1.5):
                # Now I can be sure that I found a vuln, I control the
                # time of the response.
                desc = 'ReDoS was found at: %s' % mutant.found_at()
                
                v = Vuln.from_mutant('ReDoS vulnerability', desc,
                                     severity.MEDIUM, response.id,
                                     self.get_name(), mutant)
                
                self.kb_append_uniq(self, 'redos', v)

            else:
                # The first delay existed... I must report something...
                desc = 'A potential ReDoS was found at: %s. Please review'\
                       ' manually.'
                desc = desc % mutant.found_at()
                
                i = Info('Potential ReDoS vulnerability', desc,
                         response.id, self.get_name())

                # Just printing to the debug log, we're not sure about this
                # finding and we don't want to clog the report with false
                # positives
                om.out.debug(str(i))

    def get_plugin_deps(self):
        '''
        @return: A list with the names of the plugins that should be run before
                 the current one.
        '''
        return ['infrastructure.server_header']

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds ReDoS (regular expression DoS) vulnerabilities as
        explained here:
            - http://en.wikipedia.org/wiki/ReDoS
        '''
