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
import w3af.core.data.parsers.parser_cache as parser_cache

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.kb.info import Info
from w3af.core.data.kb.info_set import InfoSet


class get_emails(GrepPlugin):
    """
    Find email accounts.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        GrepPlugin.__init__(self)

        # User configured variables
        self._only_target_domain = True
        self._already_reported = ScalableBloomFilter()

    def grep(self, request, response):
        """
        Plugin entry point, get the emails and save them to the kb.

        :param request: The HTTP request
        :param response: The HTTP response
        :return: None
        """
        try:
            document_parser = parser_cache.dpc.get_document_parser_for(response)
        except BaseFrameworkException:
            return

        analysis_data = []
        root_domain = response.get_url().get_root_domain()

        analysis_data.append(('emails', root_domain))

        if not self._only_target_domain:
            analysis_data.append(('external_emails', None))

        for kb_key, domain in analysis_data:
            self._grep_worker(request, response, document_parser, kb_key, domain)

    def _grep_worker(self, request, response, document_parser, kb_key, domain):
        emails = set(document_parser.get_emails(domain))

        for mail_address in emails:
            # Reduce false positives
            if request.sent(mail_address):
                continue

            # Email address are case insensitive
            mail_address = mail_address.lower()
            url = response.get_url()
            uniq_key = (mail_address, url)

            if uniq_key in self._already_reported:
                continue

            # Avoid duplicates
            self._already_reported.add(uniq_key)

            # Create a new info object, and report it
            desc = 'The mail account: "%s" was found at "%s".'
            desc %= (mail_address, url)

            i = Info('Email address disclosure', desc, response.id,
                     self.get_name())
            i.add_to_highlight(mail_address)
            i.set_url(url)
            i[EmailInfoSet.ITAG] = mail_address
            i['user'] = mail_address.split('@')[0]

            self.kb_append_uniq_group('emails', kb_key, i,
                                      group_klass=EmailInfoSet)

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


class EmailInfoSet(InfoSet):
    ITAG = 'mail'
    TEMPLATE = (
        'The application discloses the "{{ mail }}" email address in'
        ' {{ uris|length }} different HTTP responses. The first ten URLs'
        ' which sent the email are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )
