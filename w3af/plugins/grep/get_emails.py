"""
get_emails.py

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
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.parsers.parser_cache as parser_cache
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.kb.info import Info


class get_emails(GrepPlugin):
    """
    Find email accounts.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        GrepPlugin.__init__(self)

        # User configured variables
        self._only_target_domain = True

    def grep(self, request, response):
        """
        Plugin entry point, get the emails and save them to the kb.

        :param request: The HTTP request
        :param request: The HTTP response
        :return: None
        """
        self._grep_worker(request, response, 'emails',
                          response.get_url().get_root_domain())

        if not self._only_target_domain:
            self._grep_worker(request, response, 'external_emails')

    def _grep_worker(self, request, response, kb_key, domain=None):
        """
        Helper method for using in self.grep()

        :param request: The HTTP request
        :param response: The HTTP response
        :param kb_key: Knowledge base dict key
        :param domain: Target domain for get_emails filter
        :return: None
        """
        try:
            dp = parser_cache.dpc.get_document_parser_for(response)
        except BaseFrameworkException:
            msg = 'If I can\'t parse the document, I won\'t be able to find'\
                  '  any emails. Ignoring the response for "%s".'
            om.out.debug(msg % response.get_url())
            return

        emails = dp.get_emails(domain)

        for mail_address in emails:
            # Reduce false positives
            if request.sent(mail_address):
                continue

            # Email address are case insensitive
            mail_address = mail_address.lower()
            url = response.get_url()

            email_map = {}
            for info_obj in kb.kb.get('emails', 'emails'):
                mail_string = info_obj['mail']
                email_map[mail_string] = info_obj

            if mail_address not in email_map:
                # Create a new info object, and report it
                desc = 'The mail account: "%s" was found in: \n- %s'\
                       ' - In request with id: %s.'
                desc = desc % (mail_address, url, response.id)

                i = Info('Exposed email address', desc, response.id,
                         self.get_name())
                i.set_url(url)
                i['mail'] = mail_address
                i['url_list'] = set([url,])
                i['user'] = mail_address.split('@')[0]
                i.add_to_highlight(mail_address)
                
                self.kb_append('emails', kb_key, i)

            else:

                # Get the corresponding info object.
                i = email_map[mail_address]
                # And work
                if url not in i['url_list']:
                    # This email was already found in some other URL
                    # I'm just going to modify the url_list and the description
                    # message of the information object.
                    id_list_of_info = i.get_id()
                    id_list_of_info.append(response.id)
                    i.set_id(id_list_of_info)
                    i.set_url(url)
                    desc = i.get_desc()
                    desc += '\n- %s - In request with id: %s.'
                    desc = desc % (url, response.id)
                    i.set_desc(desc)
                    i['url_list'].add(url)

    def set_options(self, options_list):
        self._only_target_domain = options_list['only_target_domain'].get_value()

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d1 = 'Only search emails for domain of target'
        o1 = opt_factory('only_target_domain', self._only_target_domain,
                         d1, 'boolean')
        ol.add(o1)

        return ol

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page for emails, these can be used in other
        places, like bruteforce plugins, and are of great value when doing a
        complete information security assessment.
        """
