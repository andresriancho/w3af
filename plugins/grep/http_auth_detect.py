'''
http_auth_detect.py

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
import re

import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb
import core.data.kb.info as info
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity
import core.data.parsers.parser_cache as parser_cache

from core.controllers.exceptions import w3afException
from core.controllers.plugins.grep_plugin import GrepPlugin


class http_auth_detect(GrepPlugin):
    '''
    Find responses that indicate that the resource requires auth.

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        GrepPlugin.__init__(self)

        self._auth_uri_regex = re.compile('.*://[\w%]*?:[\w%]*?@[\w\.]{3,40}')

    def grep(self, request, response):
        '''
        Finds 401 or authentication URIs like http://user:pass@domain.com/

        @param request: The HTTP request object.
        @param response: The HTTP response object
        @return: None
        '''
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
        '''
        Analyze a 200 response and report any findings of http://user:pass@domain.com/
        @return: None
        '''
        #
        #   Analyze the HTTP URL
        #
        if ('@' in response.get_uri() and
                self._auth_uri_regex.match(response.get_uri().url_string)):
            # An authentication URI was found!
            v = vuln.vuln()
            v.set_plugin_name(self.get_name())
            v.set_url(response.get_url())
            v.set_id(response.id)
            desc = 'The resource: "%s" has a user and password in ' \
                'the URI.' % response.get_uri()
            v.set_desc(desc)
            v.set_severity(severity.HIGH)
            v.set_name('Basic HTTP credentials')
            v.add_to_highlight(response.get_uri().url_string)

            kb.kb.append(self, 'userPassUri', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

        #
        #   Analyze the HTTP response body
        #
        url_list = []
        try:
            DocumentParser = parser_cache.dpc.get_document_parser_for(response)
        except w3afException, w3:
            msg = 'Failed to find a suitable document parser. ' \
                'Exception: ' + str(w3)
            om.out.debug(msg)
        else:
            parsed_references, re_references = DocumentParser.get_references()
            url_list.extend(parsed_references)
            url_list.extend(re_references)

        for url in url_list:

            if ('@' in url.url_string and
                    self._auth_uri_regex.match(url.url_string)):
                v = vuln.vuln()
                v.set_plugin_name(self.get_name())
                v.set_url(response.get_url())
                v.set_id(response.id)
                msg = 'The resource: "' + response.get_url(
                ) + '" has a user and password in the'
                msg += ' body. The offending URL is: "' + url + '".'
                v.set_desc(msg)

                v.set_severity(severity.HIGH)
                v.set_name('Basic HTTP credentials')
                v.add_to_highlight(url.url_string)

                kb.kb.append(self, 'userPassUri', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _analyze_401(self, response):
        '''
        Analyze a 401 response and report it.
        @return: None
        '''
        # Get the realm
        realm = None
        for key in response.get_headers():
            if key.lower() == 'www-authenticate':
                realm = response.get_headers()[key]
                break

        if realm is None:
            # Report this strange case
            i = info.info()
            i.set_plugin_name(self.get_name())
            i.set_name('Authentication without www-authenticate header')
            i.set_url(response.get_url())
            i.set_id(response.id)
            i.set_desc('The resource: "' + response.get_url() + '" requires authentication ' +
                       '(HTTP Code 401) but the www-authenticate header is not present. This requires ' +
                       'human verification.')
            kb.kb.append(self, 'non_rfc_auth', i)

        else:
            # Report the common case, were a realm is set.
            i = info.info()
            i.set_plugin_name(self.get_name())
            if 'ntlm' in realm.lower():
                i.set_name('NTLM authentication')
            else:
                i.set_name('HTTP Basic authentication')
            i.set_url(response.get_url())
            i.set_id(response.id)
            i.set_desc('The resource: "' + response.get_url() + '" requires authentication.' +
                       ' The realm is: "' + realm + '".')
            i['message'] = realm
            i.add_to_highlight(realm)

            kb.kb.append(self, 'auth', i)

        om.out.information(i.get_desc())

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page and finds responses that indicate that the
        resource requires authentication.
        '''
