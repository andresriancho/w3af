"""
finger_google.py

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

import w3af.core.controllers.output_manager as om
import w3af.core.data.parsers.parser_cache as parser_cache

from w3af.core.data.search_engines.google import google as google
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.kb.info import Info

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.controllers.misc.is_private_site import is_private_site
from w3af.core.controllers.exceptions import RunOnce


class finger_google(InfrastructurePlugin):
    """
    Search Google using the Google API to get a list of users for a domain.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        InfrastructurePlugin.__init__(self)

        # Internal variables
        self._accounts = []
        self._google = None
        self._domain = None
        self._domain_root = None

        # User configured
        self._result_limit = 300
        self._fast_search = False

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        if is_private_site(fuzzable_request.get_url().get_domain()):
            return

        # There are no race conditions here with these attributes because of
        # @runonce
        self._domain = fuzzable_request.get_url().get_domain()
        self._domain_root = fuzzable_request.get_url().get_root_domain()
        self._google = google(self._uri_opener)

        if self._fast_search:
            self._do_fast_search()
        else:
            self._do_complete_search()

    def _do_fast_search(self):
        """
        Only search for mail addresses in the google result page.
        """
        search_string = '@' + self._domain_root
        result_page_objects = self._google.get_n_result_pages(search_string, self._result_limit)

        for result in result_page_objects:
            self._parse_document(result)

    def _do_complete_search(self):
        """
        Performs a complete search for email addresses.
        """
        search_string = '@' + self._domain_root
        google_results = self._google.search(search_string, self._result_limit)
        self.worker_pool.map(self._find_accounts, google_results)

    def _find_accounts(self, google_result):
        """
        Finds emails in google result page.

        :param google_result: GoogleResult instance
        :return: A list of valid accounts
        """
        om.out.debug('Searching for emails in: ' + google_result.URL)

        grep_res = google_result.URL.get_domain() == self._domain

        response = self._uri_opener.GET(google_result.URL,
                                        cache=True,
                                        grep=grep_res)
        self._parse_document(response)

    def _parse_document(self, response):
        """
        Parses the HTML and adds the mail addresses to the kb.
        """
        get_document_parser_for = parser_cache.dpc.get_document_parser_for

        try:
            document_parser = get_document_parser_for(response, cache=False)
        except BaseFrameworkException:
            # Failed to find a suitable parser for the document
            return

        #
        # Search for email addresses
        #
        for mail in document_parser.get_emails(self._domain_root):
            if mail not in self._accounts:
                self._accounts.append(mail)

                desc = 'The mail account: "%s" was found at: "%s".'
                desc %= (mail, response.get_uri())

                i = Info('Email account',
                         desc,
                         response.id,
                         self.get_name())
                i.set_url(response.get_uri())
                i['mail'] = mail
                i['user'] = mail.split('@')[0]
                i['url_list'] = {response.get_uri()}

                self.kb_append('emails', 'emails', i)

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()
        
        d = 'Fetch the first "result_limit" results from the Google search'
        o = opt_factory('result_limit', self._result_limit, d, 'integer')
        ol.add(o)
        
        d = ('Do a fast search, when this feature is enabled, not all mail'
             ' addresses are found')
        h = ('This method is faster, because it only searches for emails in'
             ' the small page snippet that Google shows to the user after'
             ' performing a common search.')
        o = opt_factory('fast_search', self._fast_search, d, 'boolean', help=h)
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
        self._fast_search = options_list['fast_search'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds mail addresses in google.

        Two configurable parameters exist:
            - result_limit
            - fast_search

        If fast_search is set to False, this plugin searches google for:
        "@domain.com", requests all search results and parses them in order to
        find new mail addresses. If the fast_search configuration parameter is
        set to True, only mail addresses that appear on the google result page
        are parsed and added to the list, the result links are\'nt visited.
        """
