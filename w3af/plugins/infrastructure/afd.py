"""
afd.py

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
import urllib

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import RunOnce, BaseFrameworkException
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_not_equal
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.data.kb.info import Info


class afd(InfrastructurePlugin):
    """
    Find out if the remote web server has an active filter (IPS or WAF).
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        #
        #   Internal variables
        #
        self._not_filtered = []
        self._filtered = []

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        Nothing strange, just do some GET requests to the first URL with an
        invented parameter and the custom payloads that are supposed to be
        filtered, and analyze the response.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        try:
            filtered, not_filtered = self._send_requests(fuzzable_request,
                                                         debugging_id)
        except BaseFrameworkException, bfe:
            om.out.error(str(bfe))
        else:
            self._analyze_results(filtered, not_filtered)

    def _send_requests(self, fuzzable_request, debugging_id):
        """
        Actually send the requests that might be blocked.
        :param fuzzable_request: The FuzzableRequest to modify in order to
                                     see if it's blocked
        """
        rnd_param = rand_alnum(7)
        rnd_value = rand_alnum(7)
        fmt = '%s?%s=%s'
        original_url_str = fmt % (fuzzable_request.get_url(),
                                  rnd_param,
                                  rnd_value)
        original_url = URL(original_url_str)

        try:
            http_resp = self._uri_opener.GET(original_url,
                                             cache=True,
                                             debugging_id=debugging_id)
        except BaseFrameworkException, bfe:
            msg = ('Active filter detection plugin failed to receive a'
                   ' response for the first request. The exception was: "%s".'
                   ' Can not perform analysis.')
            raise BaseFrameworkException(msg % bfe)

        orig_resp_body = http_resp.get_body()
        orig_resp_body = orig_resp_body.replace(rnd_param, '')
        orig_resp_body = orig_resp_body.replace(rnd_value, '')

        tests = []
        for offending_string in self._get_offending_strings():
            args = (fuzzable_request.get_url(), rnd_param, offending_string)
            offending_url = fmt % args
            offending_url = URL(offending_url)
            tests.append((offending_string,
                          offending_url,
                          orig_resp_body,
                          rnd_param))

        self.worker_pool.map_multi_args(self._send_and_analyze, tests)

        return self._filtered, self._not_filtered

    def _send_and_analyze(self, offending_string, offending_url,
                          original_resp_body, rnd_param):
        """
        Actually send the HTTP request.

        :return: None, everything is saved to the self._filtered and
                 self._not_filtered lists.
        """
        try:
            http_response = self._uri_opener.GET(offending_url, cache=False)
            resp_body = http_response.get_body()
        except BaseFrameworkException:
            # I get here when the remote end closes the connection
            self._filtered.append(offending_url)
        else:
            # I get here when the remote end returns a 403 or something like
            # that... So I must analyze the response body
            resp_body = resp_body.replace(offending_string, '')
            resp_body = resp_body.replace(rnd_param, '')

            if fuzzy_not_equal(resp_body, original_resp_body, 0.15):
                self._filtered.append(offending_url)
            else:
                self._not_filtered.append(offending_url)

    def _analyze_results(self, filtered, not_filtered):
        """
        Analyze the test results and save the conclusion to the kb.
        """
        if len(filtered) >= len(self._get_offending_strings()) / 5.0:
            desc = ('The remote network has an active filter. IMPORTANT: The'
                    ' result of all the other plugins will be inaccurate, web'
                    ' applications could be vulnerable but "protected" by the'
                    ' active filter.')
                   
            i = Info('Active filter detected', desc, 1, self.get_name())
            i['filtered'] = filtered
            
            kb.kb.append(self, 'afd', i)
            om.out.information(i.get_desc())

            om.out.information('The following URLs were filtered:')
            for i in filtered:
                om.out.information('- ' + i)

            if not_filtered:
                msg = 'The following URLs passed undetected by the filter:'
                om.out.information(msg)
                for i in not_filtered:
                    om.out.information('- ' + i)

        # Cleanup some memory
        self._not_filtered = []
        self._filtered = []

    def _get_offending_strings(self):
        """
        :return: A list of strings that will be filtered by most IPS devices.
        """
        res = ['../../../../etc/passwd',
               './../../../etc/motd\0html',
               'id;uname -a',
               '<? passthru("id");?>',
               '../../WINNT/system32/cmd.exe?dir+c:\\',
               'type+c:\\winnt\\repair\\sam._',
               'ps -aux;',
               '../../../../bin/chgrp nobody /etc/shadow|',
               'SELECT TOP 1 name FROM sysusers',
               'exec master..xp_cmdshell dir',
               'exec xp_cmdshell dir',
               '<script>alert(1)</script>']

        res = [urllib.quote_plus(x) for x in res]

        return res

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin sends custom requests to the remote web server in order to
        verify if the remote network is protected by an IPS or WAF.

        afd plugin detects both TCP-Connection-reset and HTTP level filters, the
        first one (usually implemented by IPS devices) is easy to verify: if afd
        requests a specially crafted URL and the connection is closed, then
        its being probably blocked by an active filter.
        
        The second protection type, usually implemented by Web Application
        Firewalls like mod_security, is a little harder to identify: first afd 
        requests a page without adding any payloads, afterwards it requests the
        same URL but with a fake parameter and customized values; if the response
        bodies differ, then its safe to say that the remote end has an active
        filter.
        """
