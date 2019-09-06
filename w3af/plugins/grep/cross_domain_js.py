"""
cross_domain_js.py

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
import w3af.core.data.parsers.parser_cache as parser_cache

from w3af import ROOT_PATH
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.info import Info
from w3af.core.data.kb.info_set import InfoSet
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import INPUT_FILE
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.misc.encoding import smart_str_ignore
from w3af.core.data.quick_match.multi_in import MultiIn


class cross_domain_js(GrepPlugin):
    """
    Find script tags with src attributes that point to a different domain.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        GrepPlugin.__init__(self)

        # User configured settings
        # Not 100% secure, but can be considered as safe in 99,9% of the cases
        # Taken from https://github.com/WPO-Foundation/webpagetest/blob/master/agent/wpthook/cdn.h#L46
        self._secure_js_file = os.path.join(ROOT_PATH, 'plugins', 'grep',
                                            'cross_domain_js',
                                            'secure-js-sources.txt')

        # Internal variables
        self._secure_domain_multi_in = None
        self._load_secure_js_file(self._secure_js_file)

    def grep(self, request, response):
        """
        Plugin entry point, verify if the HTML has <script> tags with src
        pointing to external+insecure domains.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        if self._secure_domain_multi_in is None:
            return

        if not response.is_text_or_html():
            return

        for tag in parser_cache.dpc.get_tags_by_filter(response, ('script',)):
            # pylint: disable=E1101
            script_src = tag.attrib.get('src', None)
            # pylint: enable=E1101

            if script_src is None:
                continue

            try:
                script_full_url = response.get_url().url_join(script_src)
            except ValueError:
                msg = 'Invalid URL found by cross_domain_js: "%s"'
                om.out.debug(msg % script_src)
                continue

            # More analysis methods might be added here later
            self._analyze_domain(response, script_full_url, tag)

    def _analyze_domain(self, response, script_full_url, script_tag):
        """
        Checks if the domain is the same, or if it's considered secure.
        """
        response_url = response.get_url()
        script_domain = script_full_url.get_domain()

        if script_domain == response_url.get_domain():
            return

        for _ in self._secure_domain_multi_in.query(script_domain):
            # Query the multi in to check if any if the domains we loaded
            # previously match against the script domain we found in the
            # HTML.
            #
            # It's a third party that we trust
            return

        to_highlight = script_tag.attrib.get('src')
        desc = ('The URL: "%s" has a script tag with a source that points'
                ' to a third party site ("%s"). This practice is not'
                ' recommended, the security of the current site is being'
                ' delegated to the external entity.')
        desc %= (smart_str_ignore(response_url),
                 smart_str_ignore(script_domain))

        i = Info('Cross-domain javascript source', desc,
                 response.id, self.get_name())
        i.set_url(response_url)
        i.add_to_highlight(to_highlight)
        i[CrossDomainInfoSet.ITAG] = script_domain

        self.kb_append_uniq_group(self, 'cross_domain_js', i,
                                  group_klass=CrossDomainInfoSet)

    def set_options(self, options_list):
        """
        Handle user configuration parameters.
        :return: None
        """
        secure_js_file = options_list['secure_js_file'].get_value()
        self._load_secure_js_file(secure_js_file)

    def _load_secure_js_file(self, secure_js_file):
        """
        Loads the configuration file containing the domains
        """
        if not secure_js_file:
            return

        if secure_js_file == 'None':
            return

        secure_js_domains = set()
        secure_js_domains_fh = file(secure_js_file)

        for domain in secure_js_domains_fh:
            secure_js_domains.add(domain.strip())

        self._secure_domain_multi_in = MultiIn(secure_js_domains)

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Path to file containing a list of trusted JavaScript domains'
        o = opt_factory('secure_js_file', self._secure_js_file, d, INPUT_FILE)
        ol.add(o)

        return ol

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Find script tags with src attributes that point to a different domain.

        It is important to notice that websites that depend on external
        javascript sources are delegating part of their security to those
        entities, so it is imperative to be aware of such code.
        """


class CrossDomainInfoSet(InfoSet):

    ITAG = 'domain'

    TEMPLATE = (
        'The application contains {{ uris|length }} different URLs with a'
        ' script tag which includes JavaScript source from the potentially'
        ' insecure "{{ domain }}" third party site. This practice is not'
        ' recommended because it delegates the security of the site to an'
        ' external entity. The first {{ uris|sample_count }} vulnerable URLs'
        ' are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )
