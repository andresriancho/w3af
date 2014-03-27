"""
csrf.py

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
from math import log, floor

import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.misc.levenshtein import relative_distance_boolean
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.fuzzer.mutants.headers_mutant import HeadersMutant
from w3af.core.data.kb.vuln import Vuln

COMMON_CSRF_NAMES = (
    'csrf_token',
    'CSRFName',                   # OWASP CSRF_Guard
    'CSRFToken',                  # OWASP CSRF_Guard
    'anticsrf',                   # AntiCsrfParam.java
    '__RequestVerificationToken', # AntiCsrfParam.java
    'token',
    'csrf',
    'YII_CSRF_TOKEN',             # http://www.yiiframework.com/
    'yii_anticsrf'                # http://www.yiiframework.com/
    '[_token]',                   # Symfony 2.x
    '_csrf_token',                # Symfony 1.4
    'csrfmiddlewaretoken',        # Django 1.5
)


class csrf(AuditPlugin):
    """
    Identify Cross-Site Request Forgery vulnerabilities.
    
    :author: Taras (oxdef@oxdef.info)
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        AuditPlugin.__init__(self)

        self._strict_mode = False
        self._equal_limit = 0.90

    def audit(self, freq, orig_response):
        """
        Tests a URL for CSRF vulnerabilities.

        :param freq: A FuzzableRequest
        """
        if not self._is_suitable(freq):
            return

        # Referer/Origin check
        #
        # IMPORTANT NOTE: I'm aware that checking for the referer header does
        # NOT protect the application against all cases of CSRF, but it's a
        # very good first step. In order to exploit a CSRF in an application
        # that protects using this method an intruder would have to identify
        # other vulnerabilities such as XSS or open redirects.
        #
        # TODO: This algorithm has lots of room for improvement
        if self._is_origin_checked(freq, orig_response):
            om.out.debug('Origin for %s is checked' % freq.get_url())
            return

        # Does the request have CSRF token in query string or POST payload?
        if self._find_csrf_token(freq):
            om.out.debug('Token for %s exists and was checked' % freq.get_url())
            return

        # Ok, we have found vulnerable to CSRF attack request
        msg = 'Cross Site Request Forgery has been found at: ' + freq.get_url()
        
        v = Vuln.from_fr('CSRF vulnerability', msg, severity.HIGH,
                         orig_response.id, self.get_name(), freq)
        
        self.kb_append_uniq(self, 'csrf', v)

    def _is_resp_equal(self, res1, res2):
        """
        @see: unittest for this method in test_csrf.py
        """
        if res1.get_code() != res2.get_code():
            return False

        if not relative_distance_boolean(res1.body, res2.body,
                                         self._equal_limit):
            return False

        return True

    def _is_suitable(self, freq):
        """
        For CSRF attack we need request with payload and persistent/session
        cookies.

        :return: True if the request can have a CSRF vulnerability
        """
        # Does the application send cookies?
        #
        # By checking like this we're loosing the opportunity to detect any
        # CSRF vulnerabilities in non-authenticated parts of the application
        for cookie in self._uri_opener.get_cookies():
            if freq.get_url().get_domain() in cookie.domain:
                break
        else:
            return False

        # Strict mode on/off - do we need to audit GET requests? Not always...
        if freq.get_method() == 'GET' and self._strict_mode:
            return False

        # Does the request have a payload?
        #
        # By checking like this we're loosing the opportunity to find CSRF vulns
        # in applications that use mod_rewrite. Example: A CSRF in this URL:
        # http://host.tld/users/remove/id/123
        if not freq.get_uri().has_query_string() and not freq.get_dc():
            return False

        om.out.debug('%s is suitable for CSRF attack' % freq.get_url())
        return True

    def _is_origin_checked(self, freq, orig_response):
        """
        :return: True if the remote web application verifies the Referer before
                 processing the HTTP request.
        """
        fake_ref = 'http://www.w3af.org/'
        mutant = HeadersMutant(freq.copy())
        mutant.set_var('Referer')
        mutant.set_original_value(freq.get_referer())
        mutant.set_mod_value(fake_ref)
        mutant_response = self._uri_opener.send_mutant(mutant)
        
        if not self._is_resp_equal(orig_response, mutant_response):
            return True
        
        return False

    def _find_csrf_token(self, freq):
        """
        :return: A dict with the first identified token
        """
        result = {}
        dc = freq.get_dc()
        
        for param_name in dc:
            for element_index, element_value in enumerate(dc[param_name]):
            
                if self.is_csrf_token(param_name, element_value):
                    
                    result[param_name] = element_value
                    
                    msg = 'Found CSRF token %s in parameter %s for URL %s.'
                    om.out.debug(msg % (element_value,
                                        param_name,
                                        freq.get_url()))
                    
                    return result
        
        return result

    def _is_token_checked(self, freq, token, orig_response):
        """
        Please note that this method generates lots of false positives and
        negatives. Read the github issue for more information.
        
        :see: https://github.com/andresriancho/w3af/issues/120
        :return: True if the CSRF token is NOT verified by the web application
        """
        token_pname_lst = token.keys()
        token_value = token[token_pname_lst[0]]
        
        # This will generate mutants for the original fuzzable request using
        # the reversed token value as a CSRF-token (this is a feature: we want
        # to make sure it has the same length as the original token and that
        # it has the same type: digits, hash, etc. in order to pass the first
        # trivial validations)
        #
        # Only create mutants that modify the token parameter name 
        mutants = create_mutants(freq, [token_value[::-1],], False, token_pname_lst)
        
        for mutant in mutants:
            mutant_response = self._uri_opener.send_mutant(mutant)
            if not self._is_resp_equal(orig_response, mutant_response):
                return True
            
        return False

    def is_csrf_token(self, key, value):
        # Entropy based algoritm
        # http://en.wikipedia.org/wiki/Password_strength
        min_length = 6
        min_entropy = 36

        # Check length
        if len(value) < min_length:
            return False
        
        # Check for common CSRF token names
        for common_csrf_name in COMMON_CSRF_NAMES:
            if common_csrf_name.lower() in key.lower():
                return True
    
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
        total = int(
            total_digit) * 10 + int(total_upper) * 26 + int(total_lower) * 26
        entropy = floor(log(total) * (len(value) / log(2)))
        if entropy >= min_entropy:
            if not total_spaces and total_digit:
                return True
        return False

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds Cross Site Request Forgeries (csrf) vulnerabilities.

        The simplest type of csrf is checked to be vulnerable, the web application
        must have sent a permanent cookie, and the aplicacion must have query
        string parameters.
        """
