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
import urlparse

import w3af.core.data.constants.severity as severity
import w3af.core.data.parsers.parser_cache as parser_cache

from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.kb.vuln import Vuln
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin


class global_redirect(AuditPlugin):
    """
    Find scripts that redirect the browser to any site.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    TEST_URLS = ('http://www.w3af.org/',
                 '//w3af.org')

    def __init__(self):
        AuditPlugin.__init__(self)

        # Internal variables
        self._script_re = re.compile('< *?script.*?>(.*?)< *?/ *?script *?>',
                                     re.IGNORECASE | re.DOTALL)
        self._meta_url_re = re.compile('.*?;URL=(.*)',
                                       re.IGNORECASE | re.DOTALL)

    def audit(self, freq, orig_response):
        """
        Tests an URL for global redirect vulnerabilities.

        :param freq: A FuzzableRequest object
        """
        mutants = create_mutants(freq, self.TEST_URLS)
        
        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result)

    def _analyze_result(self, mutant, response):
        """
        Analyze results of the _send_mutant method.
        """
        if self._find_redirect(response):
            desc = 'Global redirect was found at: ' + mutant.found_at()
            
            v = Vuln.from_mutant('Insecure redirection', desc, severity.MEDIUM,
                                 response.id, self.get_name(), mutant)

            self.kb_append_uniq(self, 'global_redirect', v)

    def _find_redirect(self, response):
        """
        This method checks if the browser was redirected (using a 302 code)
        or is being told to be redirected by javascript or <meta http-equiv="refresh"

        One day we should be able to identify all redirect methods:
        http://code.google.com/p/html5security/wiki/RedirectionMethods
        """
        lheaders = response.get_lower_case_headers()

        response = self._30x_code_redirect(response, lheaders) or \
                   self._refresh_redirect(response, lheaders) or \
                   self._meta_redirect(response) or \
                   self._javascript_redirect(response)

        return response

    def _30x_code_redirect(self, response, lheaders):
        """Test for 302 header redirects"""

        for header_name in ('location', 'uri'):
            if header_name in lheaders:
                header_value = lheaders[header_name]
                for test_url in self.TEST_URLS:
                    if self._domains_are_equal(header_value, test_url):
                        # The script sent a 302, and w3af followed the
                        # redirection so the URL is now the test site
                        return True

        return False

    def _domains_are_equal(self, redir_url, test_url):
        """
        :return: True if the domain name for the redir_url (the one we got
                 from the web application) and the test_url (the one we sent
                 to the application) are equal.
        """
        try:
            redir_domain = urlparse.urlparse(redir_url).netloc
            test_domain = urlparse.urlparse(test_url).netloc
            return redir_domain == test_domain
        except:
            return False

    def _refresh_redirect(self, response, lheaders):
        """Check for the *very strange* Refresh HTTP header, which looks like a
        <meta refresh> in the header context!
        http://stackoverflow.com/questions/283752/refresh-http-header
        """
        if 'refresh' in lheaders:
            refresh = lheaders['refresh']
            # Format is 0;url=my_view_page.php
            splitted_refresh = refresh.split('=', 1)
            if len(splitted_refresh) == 2:
                _, url = splitted_refresh
                for test_url in self.TEST_URLS:
                    if self._domains_are_equal(url, test_url):
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
                match_url = self._meta_url_re.match(redir)
                if match_url:
                    url = match_url.group(1)
                    for test_url in self.TEST_URLS:
                        if self._domains_are_equal(url, test_url):
                            return True

        return False

    def _javascript_redirect(self, response):
        """Test for JavaScript redirects, these are some common redirects:
             location.href = '../htmljavascript.htm';
             window.location = "http://www.w3af.com/"
             window.location.href="http://www.w3af.com/";
             location.replace('http://www.w3af.com/');
            """
        res = self._script_re.search(response.get_body())
        if res:

            url_group_re = '(%s)' % '|'.join(self.TEST_URLS)

            for script_code in res.groups():
                script_code = script_code.split('\n')
                code = []
                for i in script_code:
                    code.extend(i.split(';'))

                for line in code:
                    if re.search('(window\.location|location\.).*' + url_group_re, line):
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
        and when requesting this page, a HTTP 302 message with the location header
        to the value of the url parameter is sent in the response.

        Global redirection vulnerabilities can be found in javascript, META tags
        and 302 / 301 HTTP return codes.
        """
