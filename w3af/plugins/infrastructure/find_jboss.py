"""
find_jboss.py

Copyright 2012 Andres Riancho

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
from itertools import repeat, izip

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.threads.threadpool import one_to_many
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info import Info
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class find_jboss(InfrastructurePlugin):
    """
    Find default Jboss installations.

    :author: Nahuel Sanchez (nsanchez@bonsai-sec.com)
    """
    JBOSS_VULNS = (
        {'url': '/admin-console/',
         'name': 'JBoss Admin Console enabled',
         'desc': 'Jboss Admin Console was found!',
         'type': 'info'},
        {'url': '/jmx-console/',
         'name': 'JBoss JMX Console found',
         'desc': 'JMX Console found without Auth Enabled',
         'type': 'vuln'},
        {'url': '/status',
         'name': 'JBoss Status Servlet found',
         'desc': 'JBoss Status Servlet gives valuable information',
         'type': 'info'},
        {'url': '/web-console/ServerInfo.jsp',
         'name': 'WebConsole ServerInfo.jsp found',
         'desc': 'WebConsole ServerInfo.jsp gives valuable information',
         'type': 'info'},
        {'url': '/WebConsole/Invoker',
         'name': 'WebConsole Invoker found',
         'desc': 'JBoss WebConsole Invoker enables attackers to send any JMX '
         'command to JBoss AS',
         'type': 'vuln'},
        {'url': '/invoker/JMXInvokerServlet',
         'name': 'JMX Invoker enabled without Auth',
         'desc': 'JMX Invoker enables attackers to send any JMX command to '
         'JBoss AS',
         'type': 'vuln'}
    )

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        Checks if JBoss Interesting Directories exist in the target server.
        Also verifies some vulnerabilities.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                (among other things) the URL to test.
        """
        base_url = fuzzable_request.get_url().base_url()

        args_iter = izip(repeat(base_url), self.JBOSS_VULNS)
        otm_send_request = one_to_many(self.send_request)
        response_pool = self.worker_pool.imap_unordered(otm_send_request,
                                                        args_iter)

        for vuln_db_instance, response in response_pool:

            if is_404(response):
                continue

            vuln_url = base_url.url_join(vuln_db_instance['url'])
            name = vuln_db_instance['name']
            desc = vuln_db_instance['desc']

            if vuln_db_instance['type'] == 'info':
                o = Info(name, desc, response.id, self.get_name())
            else:
                o = Vuln(name, desc, severity.LOW, response.id, self.get_name())

            o.set_url(vuln_url)
            kb.kb.append(self, 'find_jboss', o)

            self.output_queue.put(FuzzableRequest(response.get_uri()))

    def send_request(self, base_url, vuln_db_instance):
        vuln_url = base_url.url_join(vuln_db_instance['url'])
        response = self._uri_opener.GET(vuln_url)
        return vuln_db_instance, response

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin identifies JBoss installation directories and possible
        security vulnerabilities.
        """
