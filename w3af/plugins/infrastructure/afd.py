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
from w3af.core.controllers.misc.levenshtein import relative_distance_lt
from w3af.core.data.parsers.url import URL
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
    def discover(self, fuzzable_request):
        """
        Nothing strange, just do some GET requests to the first URL with an
        invented parameter and the custom payloads that are supposed to be
        filtered, and analyze the response.

        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        try:
            filtered, not_filtered = self._send_requests(fuzzable_request)
        except BaseFrameworkException, w3:
            om.out.error(str(w3))
        else:
            self._analyze_results(filtered, not_filtered)

    def _send_requests(self, fuzzable_request):
        """
        Actually send the requests that might be blocked.
        :param fuzzable_request: The FuzzableRequest to modify in order to
                                     see if it's blocked
        """
        rnd_param = rand_alnum(7)
        rnd_value = rand_alnum(7)
        fmt = '%s?%s=%s'
        original_url_str = fmt % (fuzzable_request.get_url(),
                                  rnd_param, rnd_value)
        original_url = URL(original_url_str)

        try:
            http_resp = self._uri_opener.GET(original_url, cache=True)
        except BaseFrameworkException:
            msg = 'Active filter detection plugin failed to receive a'\
                  ' response for the first request. Can not perform analysis.'
            om.out.error(msg)
        else:
            original_response_body = http_resp.get_body()
            original_response_body = original_response_body.replace(
                rnd_param, '')
            original_response_body = original_response_body.replace(
                rnd_value, '')

            tests = []
            for offending_string in self._get_offending_strings():
                offending_URL = fmt % (fuzzable_request.get_url(),
                                       rnd_param,
                                       offending_string)
                offending_URL = URL(offending_URL)
                tests.append((offending_string, offending_URL,
                              original_response_body, rnd_param))

            self.worker_pool.map_multi_args(self._send_and_analyze, tests)

            return self._filtered, self._not_filtered

    def _send_and_analyze(self, offending_string, offending_URL,
                          original_resp_body, rnd_param):
        """
        Actually send the HTTP request.

        :return: None, everything is saved to the self._filtered and
                 self._not_filtered lists.
        """
        try:
            resp_body = self._uri_opener.GET(offending_URL,
                                             cache=False).get_body()
        except BaseFrameworkException:
            # I get here when the remote end closes the connection
            self._filtered.append(offending_URL)
        else:
            # I get here when the remote end returns a 403 or something like
            # that... So I must analyze the response body
            resp_body = resp_body.replace(offending_string, '')
            resp_body = resp_body.replace(rnd_param, '')
            if relative_distance_lt(resp_body, original_resp_body, 0.15):
                self._filtered.append(offending_URL)
            else:
                self._not_filtered.append(offending_URL)

    def _analyze_results(self, filtered, not_filtered):
        """
        Analyze the test results and save the conclusion to the kb.
        """
        if len(filtered) >= len(self._get_offending_strings()) / 5.0:
            desc = 'The remote network has an active filter. IMPORTANT: The'\
                   ' result of all the other plugins will be unaccurate, web'\
                   ' applications could be vulnerable but "protected" by the'\
                   ' active filter.'
                   
            i = Info('Active filter detected', desc, 1, self.get_name())
            i['filtered'] = filtered
            
            kb.kb.append(self, 'afd', i)
            om.out.information(i.get_desc())

            om.out.information('The following URLs were filtered:')
            for i in filtered:
                om.out.information('- ' + i)

            if not_filtered:
                om.out.information(
                    'The following URLs passed undetected by the filter:')
                for i in not_filtered:
                    om.out.information('- ' + i)

    def _get_offending_strings(self):
        """
        :return: A list of strings that will be filtered by most IPS devices.
        """
        res = []
        res.append('../../../../etc/passwd')
        res.append('./../../../etc/motd\0html')
        res.append('id;uname -a')
        res.append('<? passthru("id");?>')
        res.append('../../WINNT/system32/cmd.exe?dir+c:\\')
        res.append('type+c:\\winnt\\repair\\sam._')
        res.append('ps -aux;')
        res.append('../../../../bin/chgrp nobody /etc/shadow|')
        res.append('SELECT TOP 1 name FROM sysusers')
        res.append('exec master..xp_cmdshell dir')
        res.append('exec xp_cmdshell dir')

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
        requests the custom page and the GET method raises an exception, then
        its being probably blocked by an active filter. The second one (usually
        implemented by Web Application Firewalls like mod_security) is a little
        harder to verify: first afd requests a page without adding any offending
        parameters, afterwards it requests the same URL but with a faked
        parameter and customized values; if the response bodies differ, then its
        safe to say that the remote end has an active filter.
        """
