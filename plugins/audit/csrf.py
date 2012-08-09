'''
csrf.py

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
from math import log, floor

import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.controllers.misc.levenshtein import relative_distance_boolean
from core.data.fuzzer.fuzzer import createMutants
from core.data.fuzzer.mutantHeaders import mutantHeaders
from core.data.dc.dataContainer import DataContainer

COMMON_CSRF_NAMES = [
        'csrf_token',
        'token'
        ]

class csrf(baseAuditPlugin):
    '''
    Identify Cross-Site Request Forgery vulnerabilities.
    @author: Taras (oxdef@oxdef.info)
    '''
    
    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        self._strict_mode = False
        self._equal_limit = 0.95

    def audit(self, freq):
        '''
        Tests an URL for csrf vulnerabilities.

        @param freq: A fuzzableRequest
        '''
        suitable, orig_response = self._is_suitable(freq)
        if not suitable:
            return
        
        # Referer/Origin check 
        if self._is_origin_checked(freq, orig_response):
            om.out.debug('Origin for %s is checked' % freq.getURL())
            return
        
        # Does request has CSRF token in query string or POST payload?
        token = self._find_csrf_token(freq, orig_response)
        if token and self._is_token_checked(freq, token):
            om.out.debug('Token for %s is exist and checked' % freq.getURL())
            return
        
        # Ok, we have found vulnerable to CSRF attack request
        v = vuln.vuln(freq)
        v.setPluginName(self.getName())
        v.setId(orig_response.id)
        v.setName('CSRF vulnerability')
        v.setSeverity(severity.HIGH)
        msg = 'Cross Site Request Forgery has been found at: ' + freq.getURL()
        v.setDesc(msg)
        kb.kb.append(self, 'csrf', v)

    def _is_resp_equal(self, res1, res2):
        '''
        @see: unittest for this method in test_csrf.py
        '''
        if res1.getCode() != res2.getCode():
            return False

        if not relative_distance_boolean(res1.body, res2.body, self._equal_limit ):
            return False
        
        return True

    def _is_suitable(self, freq):
        '''
        For CSRF attack we need request with payload and persistent/session
        cookies. 
        
        @return: True if the request can have a CSRF vulnerability
        '''
        for cookie in self._uri_opener.get_cookies():
            print cookie
            if cookie.domain == freq.getURL().getDomain():
                break
        else:
            return False, None
        
        # Strict mode on/off - do we need to audit GET requests? Not always...
        if freq.getMethod() == 'GET' and not self._strict_mode:
            return False, None
        
        # Payload? 
        if not ((freq.getMethod() == 'GET' and freq.getURI().hasQueryString()) \
            or (freq.getMethod() =='POST' and len(freq.getDc()))):
                return False, None
            
        # Send the same request twice and analyze if we get the same responses
        # TODO: Ask Taras about these lines, I don't really understand.
        response1 = self._uri_opener.send_mutant(freq)
        response2 = self._uri_opener.send_mutant(freq)
        if not self._is_resp_equal(response1, response2):
            return False, None
        
        orig_response = response1
        om.out.debug('%s is suitable for CSRF attack' % freq.getURL())
        return True, orig_response

    def _is_origin_checked(self, freq, orig_response):
        om.out.debug('Testing %s for Referer/Origin checks' % freq.getURL())
        fake_ref = 'http://www.w3af.org/'
        mutant = mutantHeaders(freq.copy())
        mutant.setVar('Referer')
        mutant.setOriginalValue(freq.getReferer())
        mutant.setModValue(fake_ref)
        mutant_response = self._uri_opener.send_mutant(mutant)
        if not self._is_resp_equal(orig_response, mutant_response):
            return True
        return False

    def _find_csrf_token(self, freq):
        om.out.debug('Testing for token in %s' % freq.getURL())
        result = DataContainer()
        dc = freq.getDc()
        for k in dc:
            if self.is_csrf_token(k, dc[k][0]):
                result[k] = dc[k]
                om.out.debug('Found token %s for %s: ' % (freq.getURL(),str(result)))
                break
        return result

    def _is_token_checked(self, freq, token, orig_response):
        om.out.debug('Testing for validation of token in %s' % freq.getURL())
        mutants = createMutants(freq, ['123'], False, token.keys())
        for mutant in mutants:
            mutant_response = self._sendMutant(mutant, analyze=False)
            if not self._is_resp_equal(orig_response, mutant_response):
                return True
        return False

    def is_csrf_token(self, key, value):
        # Entropy based algoritm
        # http://en.wikipedia.org/wiki/Password_strength
        min_length = 4
        min_entropy = 36
        # Check for common CSRF token names
        if key in COMMON_CSRF_NAMES and value:
            return True
        # Check length
        if len(value) < min_length:
            return False
        # Calculate entropy
        total = 0
        total_digit = False
        total_lower = False
        total_upper = False
        total_spaces = False

        for i in value:
            if i.isdigit():
                total_digit = True
                continue
            if i.islower():
                total_lower = True
                continue
            if i.isupper():
                total_upper = True
                continue
            if i == ' ':
                total_spaces = True
                continue
        total = int(total_digit) * 10 + int(total_upper) * 26 + int(total_lower) * 26
        entropy = floor(log(total)*(len(value)/log(2)))
        if entropy >= min_entropy:
            if not total_spaces and total_digit:
                return True
        return False

    def end( self ):
        '''
        This method is called at the end, when w3afCore aint going to use this
        plugin anymore.
        '''
        self.printUniq(kb.kb.getData('csrf', 'csrf'), None)

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds Cross Site Request Forgeries (csrf) vulnerabilities.
        
        The simplest type of csrf is checked to be vulnerable, the web application
        must have sent a permanent cookie, and the aplicacion must have query
        string parameters.
        '''
