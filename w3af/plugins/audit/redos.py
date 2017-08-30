"""
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

"""
from __future__ import with_statement

import w3af.core.data.constants.severity as severity
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.kb.vuln import Vuln
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.delay_detection.aprox_delay import AproxDelay
from w3af.core.controllers.delay_detection.aprox_delay_controller import (AproxDelayController,
                                                                          EXPONENTIALLY)


class redos(AuditPlugin):
    """
    Find ReDoS vulnerabilities.

    :author: Sebastien Duquette ( sebastien.duquette@gmail.com )
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        AuditPlugin.__init__(self)

    def audit(self, freq, orig_response):
        """
        Tests an URL for ReDoS vulnerabilities using time delays.

        :param freq: A FuzzableRequest
        """
        if self.ignore_this_request(freq):
            return

        fake_mutants = create_mutants(freq, ['', ])

        for mutant in fake_mutants:
            for delay_obj in self.get_delays():
                
                adc = AproxDelayController(mutant, delay_obj, self._uri_opener,
                                           delay_setting=EXPONENTIALLY)
                success, responses = adc.delay_is_controlled()
    
                if not success:
                    continue

                # Now I can be sure that I found a vuln, we control the
                # response time with the delay
                desc = 'ReDoS was found at: %s' % mutant.found_at()
                response_ids = [r.id for r in responses]

                v = Vuln.from_mutant('ReDoS vulnerability', desc,
                                     severity.MEDIUM, response_ids,
                                     self.get_name(), mutant)

                self.kb_append_uniq(self, 'redos', v)

                # Only test regular expressions until we find a delay
                break

    def get_delays(self):
        """
        IMPORTANT NOTE: I need different instances of the delay objects in
                        order to avoid any threading issues. 
        """
        return [AproxDelay('%sX!',     'a', 10),
                AproxDelay('a@a.%sX!', 'a', 10),
                AproxDelay('%s9!',     '1', 10)]
                
    def ignore_this_request(self, freq):
        """
        We know for a fact that PHP is NOT vulnerable to this attack
        TODO: Add other frameworks that are not vulnerable!
        
        :return: True if the request should be ignored.
        """
        if 'php' in freq.get_url().get_extension().lower():
            return True
        
        # TODO: Improve the performance for this method since it's doing
        #       two potentially unnecessary SELECT statements to the DB
        #       maybe the way to avoid this is to use the observer pattern
        #       suggested here https://github.com/andresriancho/w3af/issues/54
        #       subscribe to changes to these kb locations and perform checks
        #       on local attributes which are updated only when the kb sends
        #       us some information
        for powered_by in kb.kb.raw_read('server_header', 'powered_by_string'):
            if 'php' in powered_by.lower():
                return True

        for preg_replace_vuln in kb.kb.get('preg_replace', 'preg_replace'):
            if preg_replace_vuln.get_url() == freq.get_url():
                return True
        
        return False

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before
                 the current one.
        """
        return ['infrastructure.server_header']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds ReDoS (regular expression DoS) vulnerabilities as
        explained here:
            - http://en.wikipedia.org/wiki/ReDoS
        """
