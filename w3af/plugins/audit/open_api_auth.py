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
from w3af.core.data.constants import severity
from w3af.core.data.kb.vuln import Vuln


class open_api_auth(AuditPlugin):
    """
    Checks if REST API endpoints authenticate incoming requests
    as defined in their API specification.
    See details in the plugin description below.

    Here is a list of possible enhancements:
      * Consider sending requests with other HTTP methods,
        and check that 401 or 405 error code is returned
        On the one hand, it may not look too good if we just replace the method,
        and keep the rest of the request untouched (headers, payload, etc).
        But on the other hand, the application is supposed to check HTTP method
        in the very beginning, and reject requests if the method is not supported.
        If the API spec says a particular method is supported,
        then the check should expect 401
        If the API spec says a particular method is not supported,
        then the check should expect 405 (preferred) or 401
        (should it only expect 405 in this case?).
      * Allow a user to specify response codes that the plugin should expect.
        Currently the plugin expects only 401.
        We can introduce 'expected_code_regex' configuration parameter
        which set a regex for expected response codes.
      * If the plugin is updated to send other HTTP methods (see above),
        we may want to introduce another configuration parameter
        to set expected response codes in this case.
      * Severity of identified issues may depend on response codes
        returned by the server.

    :author: Artem Smotrakov (artem.smotrakov@gmail.com)
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        AuditPlugin.__init__(self)
        self._spec = None
        self._expected_codes = [401]

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins
                 that should be run before the current one.
        """
        return ['crawl.open_api']

    def audit(self, freq, orig_response, debugging_id):
        """
        Check if an API endpoint requires authentication according to its API spec.

        :param freq: A FuzzableRequest to the API endpoint.
        :param orig_response: The HTTP response associated with the fuzzable request.
        :param debugging_id: A unique identifier for this call to audit().
        """
        # The check works only with API endpoints.
        # crawl.open_api plugin has to be called before.
        if not self._is_api_spec_available():
            om.out.debug("Could not find an API specification in the KB, skipping open_api_auth.")
            return False

        # The API spec must define authentication mechanisms.
        if not self._has_security_definitions_in_spec():
            om.out.debug("The API specification has no security definitions, skipping open_api_auth.")
            return False

        # The check only runs if the API specification
        # requires authentication for a endpoint.
        if not self._has_auth(freq):
            om.out.debug("Fuzzable request doesn't contain authentication info, skipping open_api_auth.")
            return

        # Remove auth info from the request.
        freq_with_no_auth = self._remove_auth(freq)

        # Send the request to the server, and check if access denied.
        self._uri_opener.send_mutant(freq_with_no_auth,
                                     callback=self._check_response_code,
                                     debugging_id=debugging_id)

    def _check_response_code(self, freq, response):
        """
        Check if an HTTP request contains an expected response code.

        :param freq: A FuzzableRequest to the API endpoint.
        :param response: The HTTP response associated with the fuzzable request.
        """
        if response.get_code() not in self._expected_codes:
            desc = 'A %s request without authentication information was sent to %s. ' \
                   'The server replied with unexpected HTTP response code %d (expected one of %s). ' \
                   'This is a strong indicator of a REST API authentication bypass.' \
                   % (freq.get_method(), freq.get_url(), response.get_code(), self._expected_codes)

            # Should severity depend on response codes?
            # For example, 2xx codes results to HIGH, but 4xx may be MEDIUM/LOW
            v = Vuln.from_fr('Broken authentication', desc,
                             severity.HIGH, response.id,
                             self.get_name(), freq)

            v['response_code'] = response.get_code()
            v['method'] = freq.get_method()

            self.kb_append_uniq(self, 'open_api_auth', v)

    def _has_security_definitions_in_spec(self):
        """
        :return: True if the API spec contains 'securityDefinitions' section,
                 False otherwise.
        """
        if self._spec.security_definitions:
            return True

        return False

    def _is_api_spec_available(self):
        """
        Make sure that we have API specification.
        The API spec has to be provided by crawl.open_api plugin
        which should be called before.

        The plugins use the global knowledge base to share the API spec.

        :return: True if API specification is available, False otherwise.
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
        Remove authentication info from a fuzzable request.

        The method looks for authentication info which is defined in the API spec.
        For example, if 'securityDefinitions' section defines oauth2 and apiKey methods,
        then the method will look for Authorization header and the API key
        (may be passed in a query string or header).

        :param freq: The fuzzable request to be modified.
        :return: A copy of the fuzzable request without auth info.
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
        Remove a header from a fuzzable request.

        :param freq: The fuzzable request to be updated.
        :param name: The header name.
        """
        headers = freq.get_headers()
        if headers.icontains(name):
            headers.idel(name)

    def _remove_api_key(self, freq, auth):
        """
        Remove an API key from a fuzzable request.

        :param freq: The fuzzable request to be modified.
        :param auth: An element of 'securityDefinitions' section
                     which describes the API key.
        """
        if auth.location == 'query':
            params = freq.get_url().get_params()
            del params[auth.name]
            freq.get_url().set_params(params)

        if auth.location == 'header':
            self._remove_header(freq, auth.name)

    def _get_operation_by_id(self, operation_id):
        """
        Look for an operation by its ID in the API specification.

        :param operation_id: ID of an operation.
        :return: An instance of Operation (Bravado).
        """
        for api_resource_name, resource in self._spec.resources.items():
            for operation_name, operation in resource.operations.items():
                if operation.operation_id == operation_id:
                    return operation

        return None

    @staticmethod
    def _get_operation_id(freq):
        """
        Get an operation ID which is associated with a fuzzable request.

        The method uses a mapping { method, url -> operation id }
        which should be provided by crawl.open_api plugin.

        :param freq: The fuzzable request.
        :return: An ID of the operation associated with the request.
        """
        request_to_operation_id = kb.kb.raw_read('open_api', 'request_to_operation_id')
        if not request_to_operation_id:
            return None

        key = '%s|%s' % (freq.get_method(), freq.get_url())
        if key not in request_to_operation_id:
            return None

        return request_to_operation_id[key]

    def _has_auth(self, freq):
        """
        Check if a fuzzable request contains authentication info
        according to the API specification.

        :param freq: The fuzzable request to be checked.
        :return: True if the request contains auth info, False otherwise.
        """
        for key, auth in self._spec.security_definitions.iteritems():
            if auth.type == 'basic' and self._has_basic_auth(freq):
                return True

            if auth.type == 'apiKey' and self._has_api_key(freq, auth):
                return True

            if auth.type == 'oauth2' and self._has_oauth2(freq):
                return True

        return False

    def _has_basic_auth(self, freq):
        """
        Check if a fuzzable request contains Basic auth info
        if it's allowed by the API specification.

        :param freq: The fuzzable request to be checked.
        :return: True if the request contains Basic auth info, False otherwise.
        """
        if not self._is_acceptable_auth_type(freq, 'basic'):
            return False

        return freq.get_headers().iget('Authorization', '')[0].startswith('basic')

    def _has_api_key(self, freq, auth):
        """
        Check if a fuzzable request contains an API key
        if it's allowed by the API specification.

        :param freq: The request to be checked.
        :param auth: An element of 'securityDefinitions' section
                     which describes the API key.
        :return: True if the request contains an API key, False otherwise.
        """
        if not self._is_acceptable_auth_type(freq, 'apiKey'):
            return False

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

    def _has_oauth2(self, freq):
        """
        Check if a fuzzable request contains OAuth2 info
        if it's allowed by the API specification.

        :param freq: The fuzzable request to be checked.
        :return: True if the request contains OAuth2 info, False otherwise.
        """
        if not self._is_acceptable_auth_type(freq, 'oauth2'):
            return False

        return freq.get_headers().iget('Authorization', '')[0].startswith('Bearer')

    def _is_acceptable_auth_type(self, freq, auth_type):
        """
        Check if the API specification allows a fuzzable request
        to have a specific auth info.

        :param freq: The fuzzable request to be checked.
        :param auth_type: Auth method (oauth2, apiKey or basic).
        :return: True if the API specification allows the request
                 to have the specified auth method, False otherwise.
        """
        operation_id = self._get_operation_id(freq)
        operation = self._get_operation_by_id(operation_id)
        if not operation:
            return False

        for security_spec in operation.security_specs:
            for key, value in security_spec.iteritems():
                if key not in self._spec.security_definitions:
                    # Should not happen.
                    continue

                security_definition = self._spec.security_definitions[key]
                if security_definition.type == auth_type:
                    return True

        return False

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin checks that REST API endpoints require authentication
        according to their API specification.

        OpenAPI specification offers the following structures
        to define requirements for authentication:
          * 'securityDefinitions' section describes all available authentication mechanisms.
            It offers three methods: basic, apiKey and oauth2.
          * 'security' section may be used in each operation to specify
            which authentication mechanisms the operation accepts.
          * Global 'security' section describes authentication mechanisms
            for operations which don't have their own 'security' section

        Currently the check is pretty simple:
          * Remove authentication info from the request (API key, header, etc).
          * Send the modified request to the endpoint.
          * Check if the response has 401 error code (access denied).

        A couple of important notes:
          * The plugin enables the 'crawl.open_api' plugin.
            It works only with REST API endpoints.
          * The check works only when API specification requires authentication for a endpoint.
          * The check works only if a user provided authentication info (API key, header, etc).
        """
