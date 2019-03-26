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
import copy

from math import log
from itertools import chain

import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_equal
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.fuzzer.mutants.headers_mutant import HeadersMutant
from w3af.core.data.misc.encoding import smart_str_ignore
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

    def audit(self, freq, orig_response, debugging_id):
        """
        Test URLs for CSRF vulnerabilities.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        if not self._is_suitable(freq, orig_response):
            return

        #
        # Referer / Origin check
        #
        # IMPORTANT NOTE: I'm aware that checking for the referer header does
        # NOT protect the application against all cases of CSRF, but it's a
        # very good first step.
        #
        # In order to exploit a CSRF in an application
        # that protects using this method an intruder would have to identify
        # other vulnerabilities, such as XSS or open redirects, in the same
        # domain.
        #
        # TODO: This algorithm has lots of room for improvement
        if self._is_origin_checked(freq, orig_response, debugging_id):
            om.out.debug('Origin for %s is checked' % freq.get_url())
            return

        # Does the request have CSRF token in query string or POST payload?
        if self._find_csrf_token(freq):
            return

        # Ok, we have found vulnerable to CSRF attack request
        msg = 'Cross Site Request Forgery has been found at: %s' % freq.get_url()
        
        v = Vuln.from_fr('CSRF vulnerability', msg, severity.MEDIUM,
                         orig_response.id, self.get_name(), freq)
        
        self.kb_append_uniq(self, 'csrf', v)

    def _is_resp_equal(self, response_1, response_2):
        """
        :param response_1: HTTP response 1
        :param response_2: HTTP response 2
        :see: unittest for this method in test_csrf.py
        """
        if response_1.get_code() != response_2.get_code():
            return False

        if not fuzzy_equal(response_1.body, response_2.body, self._equal_limit):
            return False

        return True

    def _is_suitable(self, freq, orig_response):
        """
        For CSRF attack we need request with payload and persistent/session
        cookies.

        :return: True if the request can have a CSRF vulnerability
        """
        #
        # Does the application send cookies?
        #
        # By performing this check we lose the opportunity to detect any
        # CSRF vulnerabilities in non-authenticated parts of the application
        #
        # Also note that the application running on freq.get_url().get_domain()
        # might be just sending us a google tracking cookie (no real session
        # cookie) and we might be returning true here.
        #
        for cookie in self._uri_opener.get_cookies():
            if freq.get_url().get_domain() in cookie.domain:
                break
        else:
            return False

        # Strict mode on/off - do we need to audit GET requests? Not always...
        if freq.get_method() == 'GET' and self._strict_mode:
            return False

        # Ignore potential CSRF in text/css or javascript responses
        content_type = orig_response.get_headers().get('content-type', None)
        if content_type in ('text/css', 'application/javascript'):
            return False

        #
        # Does the request have a payload?
        #
        # By performing this check we lose the opportunity to find CSRF
        # vulnerabilities in applications that use mod_rewrite. Example: A CSRF
        # in this URL: http://host.tld/users/remove/id/123
        #
        if not freq.get_uri().has_query_string() and not freq.get_raw_data():
            return False

        om.out.debug('%s is suitable for CSRF attack' % freq.get_url())
        return True

    def _is_origin_checked(self, freq, orig_response, debugging_id):
        """
        :return: True if the remote web application verifies the Referer before
                 processing the HTTP request.
        """
        fake_ref = 'http://www.w3af.org/'

        mutant = HeadersMutant(copy.deepcopy(freq))
        headers = mutant.get_dc()
        headers['Referer'] = fake_ref
        mutant.set_token(('Referer',))

        mutant_response = self._uri_opener.send_mutant(mutant, debugging_id=debugging_id)
        
        if not self._is_resp_equal(orig_response, mutant_response):
            return True
        
        return False

    def _find_csrf_token(self, freq):
        """
        :return: A tuple with the first identified csrf token and value
        """
        post_data = freq.get_raw_data()
        querystring = freq.get_querystring()
        
        for token in chain(post_data.iter_tokens(), querystring.iter_tokens()):
            
            if self.is_csrf_token(token.get_name(), token.get_value()):

                msg = 'Found CSRF token %s in parameter %s for URL %s.'
                om.out.debug(msg % (token.get_value(),
                                    token.get_name(),
                                    freq.get_url()))

                return token.get_name(), token.get_value()

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
        mutants = create_mutants(freq, [token_value[::-1]], False, token_pname_lst)
        
        for mutant in mutants:
            mutant_response = self._uri_opener.send_mutant(mutant)
            if not self._is_resp_equal(orig_response, mutant_response):
                return True
            
        return False

    def shannon_entropy(self, data):
        """
        Shannon entropy calculation
        http://pythonfiddle.com/shannon-entropy-calculation/
        """
        if not data:
            return 0

        entropy = 0

        for x in xrange(256):
            p_x = float(data.count(chr(x)))/len(data)
            if p_x > 0:
                entropy += - p_x * log(p_x, 2)

        return entropy

    def is_csrf_token(self, key, value):
        """
        Entropy based algorithm
        http://en.wikipedia.org/wiki/Password_strength
        """
        min_length = 5
        max_length = 512
        min_entropy = 2.4

        # Check length
        if len(value) <= min_length:
            return False

        if len(value) > max_length:
            # I have never seen a CSRF token longer than 256 bytes,
            # doubling that and checking to make sure we don't check
            # parameters which are files in multipart uploads or stuff
            # like that
            return False
        
        # Check for common CSRF token names
        for common_csrf_name in COMMON_CSRF_NAMES:
            if common_csrf_name.lower() in key.lower():
                return True
    
        # Calculate entropy
        entropy = self.shannon_entropy(smart_str_ignore(value))
        if entropy >= min_entropy:
            return True

        return False

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds Cross Site Request Forgeries (CSRF) vulnerabilities.

        The simplest type of csrf is checked to be vulnerable, the web
        application must have sent a permanent cookie, and the application must
        have query string parameters.
        """
