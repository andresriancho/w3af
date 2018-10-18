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
from w3af.core.controllers.plugins.audit_plugin import AuditPlugin

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om
from w3af.core.data.parsers.doc.open_api.specification import SpecificationHandler


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
        if self._has_no_api_spec():
            om.out.info("could not find an API specification, skip")
            return

        if self._no_security_in_spec():
            om.out.info("the API spec defines no security, skip")
            return


        # TODO The check should only work when the open api specification requires authentication for a endpoint
        #      Check for security headers according to the spec
        if self._should_skip(freq):
            return

        # TODO The check should send a request for each authenticated endpoint using the provided authentication,
        # then send it without the provided authentication and compare both.If they are similar (see fuzzy_equal)
        # then a vulnerability should be reported.

    def _analyze_result(self, mutant, response):
        """
        Analyze results of the _send_mutant method.
        """
        pass

    # TODO The check should only work when the user configures authentication (api key, headers, etc.)
    def _no_security_in_spec(self):
        """
        TODO
        :return:
        """
        return True

    def _has_no_api_spec(self):
        """
        TODO
        :return:
        """
        if self._spec:
            return False

        specification_handler = kb.kb.raw_read('open_api', 'specification_handler')
        if not specification_handler:
            return True

        self._spec = specification_handler.parse()

        if not self._spec:
            return True

        return False

    def _should_skip(self, freq):
        """
        TODO
        :return:
        """
        return True

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        TODO
        """
