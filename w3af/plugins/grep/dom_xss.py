"""
dom_xss.py

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

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.vuln import Vuln


class dom_xss(GrepPlugin):
    """
    Grep every page for traces of DOM XSS.

    :author: Andres Riancho ((andres.riancho@gmail.com))
    """

    JS_FUNCTIONS = ('document.write',
                    'document.writeln',
                    'document.execCommand',
                    'document.open',
                    'window.open',
                    'eval',
                    'window.execScript')
    
    JS_FUNCTION_CALLS = [re.compile(js_f + ' *\((.*?)\)', re.IGNORECASE)
                         for js_f in JS_FUNCTIONS]

    DOM_USER_CONTROLLED = ('document.URL',
                           'document.URLUnencoded',
                           'document.location',
                           'document.referrer',
                           'window.location',
                           )

    def __init__(self):
        GrepPlugin.__init__(self)

        # Compile the regular expressions
        self._script_re = re.compile('< *script *>(.*?)</ *script *>',
                                     re.IGNORECASE | re.DOTALL)

    def grep(self, request, response):
        """
        Plugin entry point, search for the DOM XSS vulns.
        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        if not response.is_text_or_html():
            return

        for vuln_code in self._smart_grep(response):
            desc = 'The URL: "%s" has a DOM XSS (insecure javascript code)'\
                   ' bug using: "%s".'
            desc = desc % (response.get_url(), vuln_code)
            
            v = Vuln('DOM Cross site scripting', desc,
                     severity.LOW, response.id, self.get_name())
            v.set_url(response.get_url())
            v.add_to_highlight(vuln_code)
            
            self.kb_append_uniq(self, 'dom_xss', v, filter_by='URL')

    def _smart_grep(self, response):
        """
        Search for the DOM XSS vulns using smart grep (context regex).
        :param response: The HTTP response object
        :return: list of dom xss items
        """
        res = []
        match = self._script_re.search(response.get_body())

        if not match:
            return res

        for script_code in match.groups():
            for function_re in self.JS_FUNCTION_CALLS:
                parameters = function_re.search(script_code)
                if parameters:
                    for user_controlled in self.DOM_USER_CONTROLLED:
                        if user_controlled in parameters.groups()[0]:
                            res.append(user_controlled)
        return res

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page for traces of DOM XSS.

        An interesting paper about DOM XSS
        can be found here:
            - http://www.webappsec.org/projects/articles/071105.shtml
        """
