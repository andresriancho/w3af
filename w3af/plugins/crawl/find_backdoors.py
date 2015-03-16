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
import re
import os

import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity
import w3af.core.data.kb.knowledge_base as kb

from w3af import ROOT_PATH
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.request.fuzzable_request import FuzzableRequest


# Mapping object to use in XPath search
BACKDOOR_COLLECTION = {'input': {'value': ('run', 'send', 'exec', 'execute',
                                           'run cmd', 'execute command',
                                           'run command', 'list', 'connect'),
                                 'name': ('cmd', 'command')},
                       'form': {'enctype': ('multipart/form-data',)}}

# List of known offensive words.
KNOWN_OFFENSIVE_WORDS = {'access', 'backdoor', 'cmd', 'cmdExe_Click',
                         'cmd_exec', 'command', 'connect', 'directory',
                         'directories', 'exec', 'exec_cmd', 'execute', 'eval',
                         'file', 'file upload', 'hack', 'hacked', 'hacked by',
                         'hacking', 'htaccess', 'launch command',
                         'launch shell', 'list', 'listing', 'output', 'passwd',
                         'password', 'permission', 'remote', 'reverse', 'run',
                         'runcmd', 'server', 'shell', 'socket', 'system',
                         'user', 'userfile', 'userid', 'web shell', 'webshell'}


class find_backdoors(CrawlPlugin):
    """
    Find web backdoors and web shells.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    WEBSHELL_DB = os.path.join(ROOT_PATH, 'plugins', 'crawl', 'find_backdoors',
                               'web_shells.txt')

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._analyzed_dirs = ScalableBloomFilter()

    def crawl(self, fuzzable_request):
        """
        For every directory, fetch a list of shell files and analyze the
        response.

        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        domain_path = fuzzable_request.get_url().get_domain_path()

        if domain_path not in self._analyzed_dirs:
            self._analyzed_dirs.add(domain_path)

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
            om.out.debug('Failed to GET webshell:' + web_shell_url)
        else:
            if self._is_possible_backdoor(response):
                desc = u'A web backdoor was found at: "%s"; this could' \
                       u' indicate that the server has been compromised.'
                desc %= response.get_url()

                v = Vuln(u'Potential web backdoor', desc, severity.HIGH,
                         response.id, self.get_name())
                v.set_url(response.get_url())

                kb.kb.append(self, 'backdoors', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())

                fr = FuzzableRequest.from_http_response(response)
                self.output_queue.put(fr)

    def _is_possible_backdoor(self, response):
        """
        Heuristic to infer if the content of <response> has the pattern of a
        backdoor response.

        :param response: HTTPResponse object
        :return: A bool value
        """
        if is_404(response):
            return False

        body_text = response.get_body()
        dom = response.get_dom()
        if dom is not None:
            for ele, attrs in BACKDOOR_COLLECTION.iteritems():
                for attrname, attr_vals in attrs.iteritems():
                    # Set of lowered attribute values
                    dom_attr_vals = \
                        set(n.get(attrname).lower() for n in
                            (dom.xpath('//%s[@%s]' % (ele, attrname))))

                    # If at least one elem in intersection return True
                    if dom_attr_vals & set(attr_vals):
                        return True

        # If no regex matched then try with keywords. At least 2 should be
        # contained in 'body_text' to succeed.
        #
        # TODO: Improve this for loop so that we only read the response once and
        #       match all the known offensive words "at the same time", instead
        #       of reading the same string N times (once for each item in
        #       KNOWN_OFFENSIVE_WORDS)
        times = 0
        for back_kw in KNOWN_OFFENSIVE_WORDS:
            if re.search(back_kw, body_text, re.I):
                times += 1
                if times == 2:
                    return True

        return False

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
