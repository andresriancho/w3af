"""
ria_enumerator.py

Copyright 2009 Jon Rose

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
import xml.dom.minidom

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af import ROOT_PATH

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info import Info


class ria_enumerator(CrawlPlugin):
    """
    Fingerprint Rich Internet Apps - Google Gears Manifest files, Silverlight and Flash.
    :author: Jon Rose ( jrose@owasp.org )
    """
    FILE_TAG_ATTR = {'crossdomain.xml': ('allow-access-from', 'domain'),
                     'clientaccesspolicy.xml': ('domain', 'uri')}

    def __init__(self):
        CrawlPlugin.__init__(self)

        # User configured parameters
        self._wordlist = os.path.join(ROOT_PATH, 'plugins', 'crawl',
                                      'ria_enumerator', 'common_filenames.db')

        # This is a list of common file extensions for google gears manifest:
        self._extensions = ['', '.php', '.json', '.txt', '.gears']

    @runonce(exc_class=RunOnce)
    def crawl(self, fuzzable_request, debugging_id):
        """
        Get the file and parse it.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        base_url = fuzzable_request.get_url().base_url()
        url_generator = self._url_generator(base_url, self._extensions,
                                            self._wordlist)

        # Send the requests using threads:
        self.worker_pool.map(self._send_and_check, url_generator, chunksize=10)

    def _url_generator(self, base_url, extensions, wordlist):
        """
        Based on different files and user configurations, generate the URLs that
        need to be tested.

        :return: URLs
        """
        # Google Gears
        for ext in extensions:
            for word in file(wordlist):

                manifest_url = base_url.url_join(word.strip() + ext)
                yield manifest_url

        # CrossDomain.XML
        cross_domain_url = base_url.url_join('crossdomain.xml')
        yield cross_domain_url

        # CrossAccessPolicy.XML
        client_access_url = base_url.url_join('clientaccesspolicy.xml')
        yield client_access_url

    def _send_and_check(self, url):
        """
        Analyze XML files.
        """
        response = self._uri_opener.GET(url, cache=True)

        if is_404(response):
            return

        file_name = url.get_file_name()

        om.out.debug('Checking response for %s in ria_enumerator.' % response)

        self._analyze_gears_manifest(url, response, file_name)
        self._analyze_crossdomain_clientaccesspolicy(url, response, file_name)

    def _analyze_gears_manifest(self, url, response, file_name):
        if '"entries":' not in response:
            return

        # Save it to the kb!
        desc = ('A gears manifest file was found at: "%s".'
                ' Each file should be manually reviewed for sensitive'
                ' information that may get cached on the client.')
        desc %= url

        i = Info('Gears manifest resource', desc, response.id,
                 self.get_name())
        i.set_url(url)

        kb.kb.append(self, url, i)
        om.out.information(i.get_desc())

        fr = FuzzableRequest.from_http_response(response)
        self.output_queue.put(fr)

    def _analyze_crossdomain_clientaccesspolicy(self, url, response, file_name):

        # https://github.com/andresriancho/w3af/issues/14491
        if file_name not in self.FILE_TAG_ATTR:
            return

        try:
            dom = xml.dom.minidom.parseString(response.get_body())
        except Exception:
            # Report this, it may be interesting for the final user
            # not a vulnerability per-se... but... it's information after all
            if 'allow-access-from' in response.get_body() or \
            'cross-domain-policy' in response.get_body() or \
            'cross-domain-access' in response.get_body():

                desc = 'The "%s" file at: "%s" is not a valid XML.'
                desc %= (file_name, response.get_url())

                i = Info('Invalid RIA settings file', desc, response.id,
                         self.get_name())
                i.set_url(response.get_url())

                kb.kb.append(self, 'info', i)
                om.out.information(i.get_desc())

            return

        tag, attribute = self.FILE_TAG_ATTR.get(file_name)
        url_list = dom.getElementsByTagName(tag)

        for url in url_list:
            url = url.getAttribute(attribute)

            if url == '*':
                desc = 'The "%s" file at "%s" allows flash / silverlight'\
                       ' access from any site.'
                desc %= (file_name, response.get_url())

                v = Vuln('Insecure RIA settings', desc, severity.LOW,
                         response.id, self.get_name())
                v.set_url(response.get_url())
                v.set_method('GET')

                kb.kb.append(self, 'vuln', v)
                om.out.vulnerability(v.get_desc(),
                                     severity=v.get_severity())

                fr = FuzzableRequest.from_http_response(response)
                self.output_queue.put(fr)

            else:
                desc = 'The "%s" file at "%s" allows flash / silverlight'\
                       ' access from "%s".'
                desc %= (file_name, response.get_url(), url)

                i = Info('Cross-domain allow ACL', desc, response.id,
                         self.get_name())
                i.set_url(response.get_url())
                i.set_method('GET')

                kb.kb.append(self, 'info', i)
                om.out.information(i.get_desc())

                fr = FuzzableRequest.from_http_response(response)
                self.output_queue.put(fr)

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Wordlist to use in the manifest file name brute forcing process.'
        o = opt_factory('wordlist', self._wordlist, d, 'string')
        ol.add(o)

        d = 'File extensions to use when brute forcing Gears Manifest files'
        o = opt_factory('manifestExtensions', self._extensions, d, 'list')
        ol.add(o)

        return ol

    def set_options(self, option_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param option_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        wordlist = option_list['wordlist'].get_value()
        if os.path.exists(wordlist):
            self._wordlist = wordlist

        self._extensions = option_list['manifestExtensions'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin searches for various Rich Internet Application files.  It
        currently searches for:

        Google gears manifests
            These files are used to determine which files are locally cached by
            google gears. They do not get cleared when the browser cache is
            cleared and may contain sensitive information.

        Flex crossdomain.xml
            This file stores domains which are allowed to make cross domain
            requests to the server.

        Silverlight clientaccesspolicy.xml
            This file determines which clients can access the server in place
            of the crossdomain.xml.

        Two configurable parameters exists:
            - wordlist: The wordlist to be used in the gears bruteforce process.
            - manifestExtensions: File extensions to use during manifest bruteforcing.
        """
