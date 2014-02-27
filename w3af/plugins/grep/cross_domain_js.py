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
from lxml import etree

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.info import Info

SCRIPT_SRC_XPATH = ".//script[@src]"


class cross_domain_js(GrepPlugin):
    """
    Find script tags with src attributes that point to a different domain.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        GrepPlugin.__init__(self)

        # Internal variables
        self._script_src_xpath = etree.XPath(SCRIPT_SRC_XPATH)

    def grep(self, request, response):
        """
        Plugin entry point, verify if the HTML has a form with file uploads.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        if not response.is_text_or_html():
            return
        
        url = response.get_url()        
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
            script_full_url = response.get_url().url_join(script_src)
            script_domain = script_full_url.get_domain()

            if script_domain != response.get_url().get_domain():
                desc = 'The URL: "%s" has script tag with a source that points' \
                       ' to a third party site ("%s"). This practice is not' \
                       ' recommended as security of the current site is being' \
                       ' delegated to that external entity.'
                desc = desc % (url, script_domain) 
                
                i = Info('Cross-domain javascript source', desc,
                         response.id, self.get_name())
                i.set_url(url)
                to_highlight = etree.tostring(script_src_tag)
                i.add_to_highlight(to_highlight)
                
                self.kb_append_uniq(self, 'cross_domain_js', i, 'URL')

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Find script tags with src attributes that point to a different domain.

        It is important to notice that websites that depend on external javascript
        sources are delegating part of their security to those entities, so
        it is imperative to be aware of such code.
        """
