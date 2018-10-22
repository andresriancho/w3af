"""
open_api_auth.py

Copyright 2018 Andres Riancho

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

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin


class open_api_auth(AuditPlugin):
    """
    TODO

    :author: Artem Smotrakov (artem.smotrakov@gmail.com)
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        AuditPlugin.__init__(self)
        self._spec = None

    def audit(self, freq, orig_response, debugging_id):
        """
        TODO
        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        # The check works only with API endpoints.
        # crawl.open_api plugin has to be called before.
        if not self._has_api_spec():
            om.out.information("Could not find an API specification, skip")
            return

        # The API spec must define authentication mechanisms.
        if not self._has_security_definitions_in_spec():
            om.out.information("The API spec has no security definitions, skip")
            return

        # The check only runs if the open api specification
        # requires authentication for a endpoint.
        # TODO: take into account `security` section for an operation (or there may be a global one)
        #       https://swagger.io/docs/specification/2-0/authentication/
        if not self._has_auth(freq):
            om.out.information("Request doesn't have auth info, skip")
            return

        # Remove auth info from the request
        freq_with_no_auth = self._remove_auth(freq)

        # Send the request to the server, and check if access was denied.
        self._uri_opener.send_mutant(freq_with_no_auth,
                                     callback=self._check_access_denied,
                                     debugging_id=debugging_id)

        # TODO consider sending requests with other HTTP methods,
        #      and check that 401 or 405 error code is returned
        #      On the one hand, it may not look too good if we just replace the method,
        #      and keep the rest of the request untouched (headers, payload, etc).
        #      But on the other hand, the application is supposed to check HTTP method in the very beginning,
        #      and reject requests if the method is not supported.
        #      If the API spec says a particular method is supported, then the check should expect 401
        #      If the API spec says a particular method is not supported,
        #      then the check should expect 405 (preferred) or 401 (should it only expect 405 in this case?).

        # TODO Should we compare the response with orig_response (see fuzzy_equal),
        #      and report a vulnerability if they are similar?
        #      Or, just checking the response code is enough?

    def _check_access_denied(self, freq, response):
        """
        TODO
        """
        pass

    def _has_security_definitions_in_spec(self):
        """
        TODO
        :return:
        """
        if self._spec.security_definitions:
            return True

        return False

    def _has_api_spec(self):
        """
        TODO
        :return:
        """
        if self._spec:
            return True

        specification_handler = kb.kb.raw_read('open_api', 'specification_handler')
        if not specification_handler:
            return False

        self._spec = specification_handler.parse()
        if self._spec:
            return True

        return False

    def _remove_auth(self, freq):
        """
        TODO
        :param freq:
        :return:
        """
        updated_freq = copy.deepcopy(freq)
        for key, auth in self._spec.security_definitions.iteritems():
            if auth.type == 'basic' or auth.type == 'oauth2':
                self._remove_header(updated_freq, 'Authorization')

            if auth.type == 'apiKey':
                self._remove_api_key(updated_freq, auth)

        return updated_freq

    @staticmethod
    def _remove_header(freq, name):
        """
        TODO
        :param freq:
        :return:
        """
        headers = freq.get_headers()
        if headers.icontains(name):
            headers.idel(name)

    def _remove_api_key(self, freq, auth):
        """
        TODO
        :param freq:
        :param auth:
        :return:
        """
        if auth.location == 'query':
            params = freq.get_url().get_params()
            del params[auth.name]
            freq.get_url().set_params(params)

        if auth.location == 'header':
            self._remove_header(freq, auth.name)

    def _has_auth(self, freq):
        """
        TODO
        :return:
        """
        for key, auth in self._spec.security_definitions.iteritems():
            if auth.type == 'basic' and self._has_basic_auth(freq):
                return True

            if auth.type == 'apiKey' and self._has_api_key(freq, auth):
                return True

            if auth.type == 'oauth2' and self._has_oauth2(freq):
                return True

        return False

    @staticmethod
    def _has_basic_auth(freq):
        return freq.get_headers().iget('Authorization', '')[0].startswith('basic')

    @staticmethod
    def _has_api_key(freq, auth):
        if not hasattr(auth, 'name'):
            return False

        if not hasattr(auth, 'location'):
            return False

        if auth.location == 'query':
            params = freq.get_url().get_params()
            return params and auth.name in params and params[auth.name]

        if auth.location == 'header' and freq.get_headers().iget(auth.name)[0]:
            return True

        return False

    @staticmethod
    def _has_oauth2(freq):
        return freq.get_headers().iget('Authorization', '')[0].startswith('Bearer')

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        TODO
        """
