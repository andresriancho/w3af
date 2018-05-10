"""
http_auth_detect.py

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

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity
import w3af.core.data.parsers.parser_cache as parser_cache

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.info import Info
from w3af.core.data.kb.vuln import Vuln


class http_auth_detect(GrepPlugin):
    """
    Find responses that indicate that the resource requires auth.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        GrepPlugin.__init__(self)

        self._auth_uri_regex = re.compile('.*://[\w%]*?:[\w%]*?@[\w\.]{3,40}')

    def grep(self, request, response):
        """
        Finds 401 or authentication URIs like http://user:pass@domain.com/

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        # If I have a 401 code, and this URL wasn't already reported...
        if response.get_code() == 401:

            # Doing this after the other if in order to be faster.
            already_reported = [i.get_url().get_domain_path() for i in
                                kb.kb.get('http_auth_detect', 'auth')]
            if response.get_url().get_domain_path() not in already_reported:

                # Perform all the work in this method
                self._analyze_401(response)

        elif response.is_text_or_html():

            # I get here for "normal" HTTP 200 responses
            self._find_auth_uri(response)

    def _find_auth_uri(self, response):
        """
        Analyze a 200 response and report any findings of http://user:pass@domain.com/
        :return: None
        """
        #
        #   Analyze the HTTP URL
        #
        if self._url_has_auth(response.get_uri()):
            # An authentication URI was found!
            desc = ('The resource: "%s" has a user and password in'
                    ' the URI.')
            desc %= response.get_uri()
            v = Vuln('Basic HTTP credentials', desc, severity.HIGH,
                     response.id, self.get_name())

            v.set_url(response.get_url())
            v.add_to_highlight(response.get_uri().url_string)

            kb.kb.append(self, 'userPassUri', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

        #
        #   Analyze the HTTP response body
        #
        url_list = []
        try:
            document_parser = parser_cache.dpc.get_document_parser_for(response)
        except BaseFrameworkException, e:
            msg = 'Failed to find a suitable document parser. Exception: "%s"'
            om.out.debug(msg % e)
        else:
            parsed_references, re_references = document_parser.get_references()
            url_list.extend(parsed_references)
            url_list.extend(re_references)

        for url in url_list:

            if self._url_has_auth(url):

                desc = ('The resource: "%s" has a user and password in the'
                        ' body. The offending URL is: "%s".')
                desc %= (response.get_url(), url)
                
                v = Vuln('Basic HTTP credentials', desc,
                         severity.HIGH, response.id, self.get_name())

                v.set_url(response.get_url())
                v.add_to_highlight(url.url_string)

                kb.kb.append(self, 'userPassUri', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _url_has_auth(self, url):
        if '@' not in url.url_string:
            return False

        if not self._auth_uri_regex.match(url.url_string):
            return False

        return True

    def _get_realm(self, response):
        for key in response.get_headers():
            if key.lower() == 'www-authenticate':
                realm = response.get_headers()[key]
                return realm
        
        return None
        
    def _report_no_realm(self, response):
        # Report this strange case
        desc = ('The resource: "%s" requires authentication (HTTP Code'
                ' 401) but the www-authenticate header is not present.'
                ' This requires human verification.')
        desc %= response.get_url()
        i = Info('Authentication without www-authenticate header', desc,
                 response.id, self.get_name())
        i.set_url(response.get_url())

        kb.kb.append(self, 'non_rfc_auth', i)
        om.out.information(i.get_desc())
        
    def _analyze_401(self, response):
        """
        Analyze a 401 response and report it.
        :return: None
        """
        realm = self._get_realm(response)
        
        if realm is None:
            self._report_no_realm(response)
            return
        
        insecure = response.get_url().get_protocol() == 'http'
        vuln_severity = severity.HIGH if insecure else severity.LOW
        
        desc = 'The resource: "%s" requires HTTP authentication'
        if insecure:
            desc += (' over a non-encrypted channel, which allows'
                     ' potential intruders to sniff traffic and capture'
                     ' valid credentials.')
        else:
            desc += '.'
        
        desc += ' The received authentication realm is: "%s".'
        desc = desc % (response.get_url(), realm)
        
        # Report the common case, were a realm is set.
        if 'ntlm' in realm.lower():
            
            v = Vuln('NTLM authentication', desc,
                     vuln_severity, response.id, self.get_name())

        else:
            v = Vuln('HTTP Basic authentication', desc,
                     vuln_severity, response.id, self.get_name())

        v.set_url(response.get_url())
        v['message'] = realm
        v.add_to_highlight(realm)

        kb.kb.append(self, 'auth', v)
        om.out.information(v.get_desc())

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page and finds responses that indicate that the
        resource requires authentication.
        """
