"""
global_redirect.py

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
import w3af.core.data.parsers.parser_cache as parser_cache

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.kb.vuln import Vuln
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin


class global_redirect(AuditPlugin):
    """
    Find scripts that redirect the browser to any site.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    TEST_DOMAIN = 'w3af.org'

    EXTENDED_PAYLOADS = None
    BASIC_PAYLOADS = {'http://www.%s/' % TEST_DOMAIN,
                      '//%s' % TEST_DOMAIN}

    SCRIPT_RE = re.compile('<script.*?>(.*?)</script>', re.IGNORECASE | re.DOTALL)
    META_URL_RE = re.compile('.*?; *?URL *?= *?(.*)', re.IGNORECASE | re.DOTALL)

    JS_REDIR_GENERIC_FMT = ['window\.location.*?=.*?["\'].*?%s.*?["\']',
                            '(self|top)\.location.*?=.*?["\'].*?%s.*?["\']',
                            'window\.location\.(replace|assign)\(["\'].*?%s.*?["\']\)']
    REDIR_TO_TEST_DOMAIN_JS_RE = [re.compile(r % TEST_DOMAIN) for r in JS_REDIR_GENERIC_FMT]
    JS_REDIR_RE = [re.compile(r % '') for r in JS_REDIR_GENERIC_FMT]

    def audit(self, freq, orig_response, debugging_id):
        """
        Tests an URL for global redirect vulnerabilities.

        When the original response contained a redirect we send more payloads
        to increase coverage.

        When the original response doesn't contain a redirect we only send
        the basic payloads.

        :param freq: A FuzzableRequest object
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        #
        #   Always send the most basic tests
        #
        self._find_open_redirect_with_payloads(freq, self.BASIC_PAYLOADS, debugging_id)

        #
        #   Send the more complex tests only if the original response was a redirect
        #
        if self._response_has_redirect(orig_response):
            extended_payloads = self._get_extended_payloads(freq)
            self._find_open_redirect_with_payloads(freq, extended_payloads, debugging_id)

    def _response_has_redirect(self, orig_response):
        """
        :param freq: The fuzzable request sent by the core
        :param orig_response: The HTTP response associated with the fuzzable request
        :return: True if the response has some type of redirect
        """
        #
        #   Check the response headers
        #
        lower_case_headers = orig_response.get_lower_case_headers()
        for header_name in ('location', 'uri', 'refresh'):
            if header_name in lower_case_headers:
                return True

        #
        #   Check javascript redirects
        #
        for statement in self._extract_script_code(orig_response):
            for js_redir_re in self.JS_REDIR_RE:
                if js_redir_re.search(statement):
                    return True

        #
        #   Check the HTTP response body meta tags
        #
        try:
            dp = parser_cache.dpc.get_document_parser_for(orig_response)
        except BaseFrameworkException:
            # Failed to find a suitable parser for the document
            return False
        else:
            # Any redirect will work for us here
            if dp.get_meta_redir():
                return True

        return False

    def _find_open_redirect_with_payloads(self, freq, payloads, debugging_id):
        """
        Find open redirects in `freq` using `payloads`

        :param freq: The fuzzable request sent by the core
        :param payloads: The payloads as strings
        :param debugging_id: A unique identifier for this call to audit()
        """
        mutants = create_mutants(freq, payloads)

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result,
                                      debugging_id=debugging_id)

    def _get_extended_payloads(self, freq):
        """
        Create payloads based on the fuzzable request

        Note that the payloads will be the same during the whole scan because w3af
        only scans one domain at the time, and the extended payloads are based on
        the host header of the fuzzable request.

        :param freq: The fuzzable request sent by the core
        :return: The extended payloads to send to the remote server
        """
        # cache
        if self.EXTENDED_PAYLOADS:
            return self.EXTENDED_PAYLOADS

        netloc = freq.get_uri().get_net_location()
        netloc = netloc.split(':')[0]
        args = (netloc, self.TEST_DOMAIN)

        extended_payloads = set()
        extended_payloads.update(['%s.%s' % args,
                                  '//%s.%s/' % args,
                                  'http://%s.%s/' % args,
                                  'https://%s.%s/' % args,
                                  '%s@%s' % args,
                                  '//%s@%s' % args,
                                  'http://%s@%s' % args,
                                  'https://%s@%s' % args])

        self.EXTENDED_PAYLOADS = extended_payloads

        return extended_payloads

    def _analyze_result(self, mutant, response):
        """
        Analyze results of the _send_mutant method.
        """
        if self._find_redirect(response):
            desc = 'Global redirect was found at: ' + mutant.found_at()
            
            v = Vuln.from_mutant('Insecure redirection', desc, severity.MEDIUM,
                                 response.id, self.get_name(), mutant)

            self.kb_append_uniq(self, 'global_redirect', v)

    def _domain_equals_test_domain(self, redir_url):
        """
        :return: True if we control the domain for the redirect target
        """
        try:
            redir_domain = URL(redir_url).get_domain()
            return redir_domain.endswith(self.TEST_DOMAIN)
        except:
            return False

    def _find_redirect(self, response):
        """
        This method checks if the browser was redirected (using a 302 code)
        or is being told to be redirected by javascript or
        <meta http-equiv="refresh"

        One day we should be able to identify all redirect methods:
        http://code.google.com/p/html5security/wiki/RedirectionMethods
        """
        lheaders = response.get_lower_case_headers()

        return self._30x_code_redirect(response, lheaders) or \
               self._refresh_redirect(response, lheaders) or \
               self._meta_redirect(response) or \
               self._javascript_redirect(response)

    def _30x_code_redirect(self, response, lheaders):
        """
        Test for 302 header redirects
        """
        for header_name in ('location', 'uri'):
            if header_name in lheaders:
                header_value = lheaders[header_name]
                header_value = header_value.strip()

                if self._domain_equals_test_domain(header_value):
                    # The script sent a 302 and the header contains the test URL
                    return True

        return False

    def _refresh_redirect(self, response, lheaders):
        """
        Check for the *very strange* Refresh HTTP header, which looks like a
        `<meta refresh>` in the header context!

        The value for the header is: `0;url=my_view_page.php`

        :see: http://stackoverflow.com/questions/283752/refresh-http-header
        """
        if 'refresh' not in lheaders:
            return False

        refresh = lheaders['refresh']
        split_refresh = refresh.split('=', 1)

        if len(split_refresh) != 2:
            return False

        _, url = split_refresh
        if self._domain_equals_test_domain(url):
            return True

        return False

    def _meta_redirect(self, response):
        """
        Test for meta redirects
        """
        try:
            dp = parser_cache.dpc.get_document_parser_for(response)
        except BaseFrameworkException:
            # Failed to find a suitable parser for the document
            return False
        else:
            for redir in dp.get_meta_redir():
                match_url = self.META_URL_RE.match(redir)
                if match_url:
                    url = match_url.group(1)
                    if self._domain_equals_test_domain(url):
                        return True

        return False

    def _extract_script_code(self, response):
        """
        This method receives an HTTP response and yields lines of <script> code

        For example, if the response contains:
            <script>
                var x = 1;
            </script>
            <a ...>
            <script>
                var y = 1; alert(1);
            </script>

        The method will yield three strings:
            var x = 1;
            var y = 1;
            alert(1);

        :return: Lines of javascript code
        """
        mo = self.SCRIPT_RE.search(response.get_body())

        if mo is not None:

            for script_code in mo.groups():
                script_code = script_code.split('\n')

                for line in script_code:
                    for statement in line.split(';'):
                        if statement:
                            yield statement

    def _javascript_redirect(self, response):
        """
        Test for JavaScript redirects, these are some common redirects:

            // These also work without the `window.` at the beginning
            window.location = "http://www.w3af.org/";
            window.location.href = "http://www.w3af.org/";
            window.location.replace("http://www.w3af.org");
            window.location.assign('http://www.w3af.org');

            self.location = 'http://www.w3af.org';
            top.location = 'http://www.w3af.org';

            // jQuery
            $(location).attr('href', 'http://www.w3af.org');
            $(window).attr('location', 'http://www.w3af.org');
            $(location).prop('href', 'http://www.w3af.org');

            // Only for old IE
            window.navigate('http://www.w3af.org');
        """
        for statement in self._extract_script_code(response):
            if self.TEST_DOMAIN not in statement:
                continue

            for redir_to_test_domain_re in self.REDIR_TO_TEST_DOMAIN_JS_RE:
                if redir_to_test_domain_re.search(statement):
                    return True

        return False

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds global redirection vulnerabilities. This kind of bugs
        are used for phishing and other identity theft attacks. A common example
        of a global redirection would be a script that takes a "url" parameter
        and when requesting this page, a HTTP 302 message with the location
        header to the value of the url parameter is sent in the response.

        Global redirection vulnerabilities can be found in javascript, META tags
        and 302 / 301 HTTP return codes.
        """
