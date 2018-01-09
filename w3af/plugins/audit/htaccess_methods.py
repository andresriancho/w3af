"""
htaccess_methods.py

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
import w3af.core.data.constants.severity as severity
import w3af.core.data.constants.response_codes as http_constants

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.vuln import Vuln


class htaccess_methods(AuditPlugin):
    """
    Find misconfigurations in Apache's "<LIMIT>" configuration.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    AUTH_CODES = {http_constants.UNAUTHORIZED, http_constants.FORBIDDEN}
    SUCCESS_CODES = {http_constants.FOUND,
                     http_constants.MOVED_PERMANENTLY,
                     http_constants.OK}

    def __init__(self):
        AuditPlugin.__init__(self)
        self._already_tested = ScalableBloomFilter()

    def audit(self, freq, orig_response, debugging_id):
        """
        Tests an URL for htaccess misconfigurations.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        url = freq.get_url()

        if url in self._already_tested:
            return

        self._already_tested.add(url)
        response = self._uri_opener.GET(freq.get_url(), cache=True)

        if response.get_code() in self.AUTH_CODES:
            self._check_methods(url, debugging_id)

    def _check_methods(self, url, debugging_id):
        """
        Perform some requests in order to check if we are able to retrieve
        some data with methods that may be wrongly enabled.
        """
        allowed_methods = []
        for method in ['GET', 'POST', 'ABCD', 'HEAD']:
            method_functor = getattr(self._uri_opener, method)
            try:
                response = apply(method_functor, (url,), {'debugging_id': debugging_id})
                code = response.get_code()
            except:
                pass
            else:
                if code in self.SUCCESS_CODES:
                    allowed_methods.append((method, response.id))

        if len(allowed_methods) > 0:
            
            response_ids = [i for m, i in allowed_methods]
            methods = ', '.join([m for m, i in allowed_methods]) + '.'
            desc = ('The resource: "%s" requires authentication but the access'
                    ' is misconfigured and can be bypassed using these'
                    ' methods: %s')
            desc %= (url, methods)
            
            v = Vuln('Misconfigured access control', desc,
                     severity.MEDIUM, response_ids, self.get_name())

            v.set_url(url)
            v['methods'] = allowed_methods
            
            self.kb_append(self, 'auth', v)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds .htaccess misconfigurations in the LIMIT configuration
        parameter.

        This plugin is based on a paper written by Frame and madjoker from
        kernelpanik.org. The paper is called : "htaccess: bilbao method exposed"

        The idea of the technique (and the plugin) is to exploit common
        misconfigurations of .htaccess files like this one:

            <LIMIT GET>
                require valid-user
            </LIMIT>

        The configuration only allows authenticated users to perform GET
        requests, but POST requests (for example) can be performed by any user.
        """
