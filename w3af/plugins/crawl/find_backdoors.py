"""
find_backdoors.py

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
import os

import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity
import w3af.core.data.kb.knowledge_base as kb

from w3af import CRAWL_PATH
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.quick_match.multi_re import MultiRE


class find_backdoors(CrawlPlugin):
    """
    Find web backdoors and web shells.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    WEBSHELL_DB = os.path.join(CRAWL_PATH, 'find_backdoors', 'web_shells.txt')
    SIGNATURE_DB = os.path.join(CRAWL_PATH, 'find_backdoors', 'signatures.txt')

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._analyzed_dirs = ScalableBloomFilter()
        self._signature_re = None

    def setup(self):
        with self._plugin_lock:
            if self._signature_re is not None:
                return

            signatures = self._read_signatures()
            self._signature_re = MultiRE(signatures, hint_len=2)

    def _read_signatures(self):
        for line in file(self.SIGNATURE_DB):
            line = line.strip()

            if not line:
                continue

            if line.startswith('#'):
                continue

            yield (line, 'Backdoor signature')

    def crawl(self, fuzzable_request, debugging_id):
        """
        For every directory, fetch a list of shell files and analyze the
        response.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        domain_path = fuzzable_request.get_url().get_domain_path()

        if domain_path in self._analyzed_dirs:
            return

        self._analyzed_dirs.add(domain_path)

        self.setup()

        # Read the web shell database
        web_shells = self._iter_web_shells()

        # Send the requests using threads:
        args_iter = (domain_path.url_join(fname) for fname in web_shells)
        self.worker_pool.map(self._check_if_exists, args_iter)

    def _iter_web_shells(self):
        """
        :yield: lines from the web shell DB
        """
        for line in file(self.WEBSHELL_DB):
            line = line.strip()

            if line.startswith('#'):
                continue

            if not line:
                continue

            yield line

    def _check_if_exists(self, web_shell_url):
        """
        Check if the file exists.

        :param web_shell_url: The URL to check
        """
        try:
            response = self._uri_opener.GET(web_shell_url, cache=True)
        except BaseFrameworkException:
            om.out.debug('Failed to GET webshell: %s' % web_shell_url)
            return

        signature = self._match_signature(response)
        if signature is None:
            return

        desc = (u'An HTTP response matching the web backdoor signature'
                u' "%s" was found at: "%s"; this could indicate that the'
                u' server has been compromised.')
        desc %= (signature, response.get_url())

        # It's probability is higher if we found a long signature
        _severity = severity.HIGH if len(signature) > 8 else severity.MEDIUM

        v = Vuln(u'Potential web backdoor', desc, _severity,
                 response.id, self.get_name())
        v.set_url(response.get_url())

        kb.kb.append(self, 'backdoors', v)
        om.out.vulnerability(v.get_desc(), severity=v.get_severity())

        fr = FuzzableRequest.from_http_response(response)
        self.output_queue.put(fr)

    def _match_signature(self, response):
        """
        Heuristic to infer if the content of <response> has the pattern of a
        backdoor response.

        :param response: HTTPResponse object
        :return: A bool value
        """
        body_text = response.get_body()
        
        for match, _, _, _ in self._signature_re.query(body_text):
            match_string = match.group(0)
            return match_string

        return None

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin searches for web shells in the directories that are sent as
        input. For example, if the input is:
            - http://host.tld/w3af/f00b4r.php

        The plugin will perform these requests:
            - http://host.tld/w3af/c99.php
            - http://host.tld/w3af/cmd.php
            ...
            - http://host.tld/w3af/webshell.php
        """
