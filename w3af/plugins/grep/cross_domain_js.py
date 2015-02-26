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

from lxml import etree

import w3af.core.controllers.output_manager as om

from w3af import ROOT_PATH
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.info import Info
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import INPUT_FILE
from w3af.core.data.options.option_list import OptionList

SCRIPT_SRC_XPATH = ".//script[@src]"


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
        self._script_src_xpath = etree.XPath(SCRIPT_SRC_XPATH)
        self._secure_js_domains = []
        self._load_secure_js_file(self._secure_js_file)

    def grep(self, request, response):
        """
        Plugin entry point, verify if the HTML has <script> tags with src
        pointing to external+insecure domains.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        if not response.is_text_or_html():
            return
        
        dom = response.get_dom()

        # In some strange cases, we fail to normalize the document
        if dom is None:
            return
        
        # Loop through script inputs tags
        for script_src_tag in self._script_src_xpath(dom):

            # This should be always False due to the XPATH we're using
            # but you never know...
            if not 'src' in script_src_tag.attrib:
                continue

            script_src = script_src_tag.attrib['src']
            try:
                script_full_url = response.get_url().url_join(script_src)
            except ValueError:
                msg = 'Invalid URL found by cross_domain_js: "%s"'
                om.out.debug(msg % script_src)
                continue

            # More analysis methods might be added here later
            self._analyze_domain(response, script_full_url, script_src_tag)

    def _analyze_domain(self, response, script_full_url, script_src_tag):
        """
        Checks if the domain is the same, or if it's considered secure.
        """
        url = response.get_url()
        script_domain = script_full_url.get_domain()

        if script_domain != response.get_url().get_domain():

            for secure_domain in self._secure_js_domains:
                if script_domain.endswith(secure_domain):
                    # It's a third party that we trust
                    return

            desc = 'The URL: "%s" has a script tag with a source that points' \
                   ' to a third party site ("%s"). This practice is not' \
                   ' recommended, the security of the current site is being' \
                   ' delegated to the external entity.'
            desc = desc % (url, script_domain)

            i = Info('Cross-domain javascript source', desc,
                     response.id, self.get_name())
            i.set_url(url)
            to_highlight = etree.tostring(script_src_tag)
            i.add_to_highlight(to_highlight)

            self.kb_append_uniq(self, 'cross_domain_js', i, 'URL')

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
        if secure_js_file and not secure_js_file == 'None':
            # Always zero the configured domains before we start
            self._secure_js_domains = []
            self._secure_js_file = secure_js_file

            secure_js_fh = file(secure_js_file)
            for domain in secure_js_fh:
                self._secure_js_domains.append(domain.strip())

            # Remove any duplicates
            self._secure_js_domains = list(set(self._secure_js_domains))

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
