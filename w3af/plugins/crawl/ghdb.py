"""
ghdb.py

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
import os.path
import random
import xml.dom.minidom

import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity
import w3af.core.data.kb.knowledge_base as kb

from w3af import ROOT_PATH

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.controllers.misc.is_private_site import is_private_site
from w3af.core.controllers.exceptions import BaseFrameworkException, RunOnce

from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.search_engines.google import google as google
from w3af.core.data.kb.vuln import Vuln


class ghdb(CrawlPlugin):
    """
    Search Google for vulnerabilities in the target site.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._ghdb_file = os.path.join(ROOT_PATH, 'plugins', 'crawl',
                                       'ghdb', 'GHDB.xml')

        # User configured variables
        self._result_limit = 300

    @runonce(exc_class=RunOnce)
    def crawl(self, fuzzable_request, debugging_id):
        """
        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                (among other things) the URL to test.
        """
        # Get the domain and set some parameters
        domain = fuzzable_request.get_url().get_domain()

        if is_private_site(domain):
            msg = ('There is no point in searching google for "site:%s".'
                   ' Google does not index private pages.')
            om.out.information(msg % domain)
            return

        self._do_clasic_GHDB(domain)

    def _do_clasic_GHDB(self, domain):
        """
        In classic GHDB, i search google for every term in the ghdb.
        """
        self._google_se = google(self._uri_opener)

        google_hack_list = self._read_ghdb()
        # Don't get discovered by google [at least try...] and avoid dups
        random.shuffle(google_hack_list)
        google_hack_set = set(google_hack_list)

        for gh in google_hack_set:
            search_term = 'site:%s %s' % (domain, gh.search)
            try:
                self._classic_worker(gh, search_term)
            except BaseFrameworkException, w3:
                # Google is saying: "no more automated tests".
                om.out.error('GHDB exception: "' + str(w3) + '".')
                break

    def _classic_worker(self, gh, search_term):
        """
        Perform the searches and store the results in the kb.
        """
        google_list = self._google_se.get_n_results(search_term, 9)

        for result in google_list:
            # I found a vuln in the site!
            response = self._uri_opener.GET(result.URL, cache=True)
            if not is_404(response):
                desc = ('ghdb plugin found a vulnerability at URL: "%s".'
                        ' According to GHDB the vulnerability description'
                        ' is "%s".')
                desc %= (response.get_url(), gh.desc)
                
                v = Vuln('Google hack database match', desc,
                         severity.MEDIUM, response.id, self.get_name())
                v.set_url(response.get_url())
                v.set_method('GET')

                kb.kb.append(self, 'vuln', v)
                om.out.vulnerability(v.get_desc(), severity=severity.LOW)

                # Create the fuzzable requests
                fr = FuzzableRequest(response.get_url())
                self.output_queue.put(fr)

    def _read_ghdb(self):
        """
        :return: Reads the ghdb.xml file and returns a list of GoogleHack
                 objects.
        """
        try:
            ghdb_fd = file(self._ghdb_file)
        except Exception, e:
            msg = 'Failed to open ghdb file: "%s", error: "%s".'
            raise BaseFrameworkException(msg % (self._ghdb_file, e))

        try:
            dom = xml.dom.minidom.parseString(ghdb_fd.read())
        except Exception, e:
            msg = 'Failed to parse XML file: "%s", error: "%s".'
            raise BaseFrameworkException(msg % (self._ghdb_file, e))

        res = []

        for signature in dom.getElementsByTagName("signature"):
            if len(signature.childNodes) != 6:
                msg = ('There is a corrupt signature in the GHDB. The error was'
                       ' found in the following XML code: "%s".')
                om.out.debug(msg % signature.toxml())
                continue

            try:
                query_string = signature.childNodes[4].childNodes[0].data

            except Exception, e:
                msg = ('There is a corrupt signature in the GHDB. No query '
                       ' string was found in the following XML code: "%s".')
                om.out.debug(msg % signature.toxml())
                continue

            try:
                desc = signature.childNodes[5].childNodes[0].data
            except:
                desc = 'No description provided by GHDB.'

            gh = GoogleHack(query_string, desc)
            res.append(gh)

        return res

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Fetch the first "result_limit" results from the Google search'
        o = opt_factory('result_limit', self._result_limit, d, 'integer')
        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._result_limit = options_list['result_limit'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds possible vulnerabilities using google.

        One configurable parameter exist:
            - result_limit

        Using the google hack database released by Exploit-DB.com, this
        plugin searches Google for possible vulnerabilities in the target
        domain.

        Special thanks go to the guys at http://www.exploit-db.com/ for
        maintaining the GHDB and letting us use this information.
        """


class GoogleHack(object):
    def __init__(self, search, desc):
        self.search = search
        self.desc = desc

    def __eq__(self, other):
        return self.search == other.search
