"""
form_cleartext_password.py

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
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.vuln import Vuln
from w3af.core.controllers.exceptions import BaseFrameworkException
import w3af.core.data.parsers.parser_cache as parser_cache
import w3af.core.data.constants.severity as severity

# Find all input elements which type's lower-case value
# equals-case-sensitive 'password'

class form_cleartext_password(GrepPlugin):
    """
    Finds forms with password inputs on every page and checks if they
    are secure.
    :author: Dmitry Roshchin (nixwizard@gmail.com)
    """

    def __init__(self):
        GrepPlugin.__init__(self)

    def grep(self, request, response):
        """
        Plugin entry point, test existence of HTML forms containing
        password-type inputs.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, all results are saved in the kb.
        """
        url = request.get_url()
        proto = url.get_protocol()
        url_string = url.url_string

        try:
            dp = parser_cache.dpc.get_document_parser_for(response)
        except BaseFrameworkException:
            # Failed to find a suitable parser for the document
            return

        for form in dp.get_forms():
            for p in form.keys():
                type = form._types.get(p)
                if type == 'password':
                    action = form.get_action()
                    action_proto = action.get_protocol()
                    # form is to be submitted over http
                    if action_proto == 'http':
                        desc = 'The the URL: "%s" has an insecure <form> ' \
                               'element and is vulnerable to insecure ' \
                               'password submission over HTTP!'
                        desc = desc % url_string
                        v = Vuln('Insecure password submission over HTTP', desc,
                                 severity.MEDIUM, response.id, self.get_name())
                        v.set_url(response.get_url())
                        self.kb_append_uniq(self,
                                            'form_cleartext_password', v)
                        break
                    else:
                        #form was recieved over http
                        if proto == "http":
                            desc = 'The the URL: "%s" delivered over http ' \
                                   'and has <form> element with password ' \
                                   'input is vulnerable to MITM!'
                            desc = desc % url_string
                            v = Vuln('MITM', desc,
                                     severity.MEDIUM, response.id,
                                     self.get_name())
                            self.kb_append_uniq(self,
                                                'form_cleartext_password',v)
                            break

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page for forms with password-type inputs
        and checks if it is vulnerable to either insecure password
        submission over HTTP or MITM
        """