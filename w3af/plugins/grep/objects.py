"""
objects.py

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


class objects(GrepPlugin):
    """
    Grep every page for objects and applets.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        GrepPlugin.__init__(self)

        # Compile the XPATH
        self._tag_xpath = etree.XPath('//object | //applet')
        self._tag_names = ('object', 'applet')

    def grep(self, request, response):
        """
        Plugin entry point. Parse the object tags.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        url = response.get_url()
        dom = response.get_dom()

        if response.is_text_or_html() and dom is not None:

            elem_list = self._tag_xpath(dom)
            for element in elem_list:

                tag_name = element.tag
                
                desc = 'The URL: "%s" has an "%s" tag. We recommend you download'\
                      ' the client side code and analyze it manually.'
                desc = desc % (response.get_uri(), tag_name)

                i = Info('Browser plugin content', desc, response.id,
                         self.get_name())
                i.set_url(url)
                i.add_to_highlight(tag_name)

                self.kb_append_uniq(self, tag_name, i, 'URL')

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page for applets and other types of objects.
        """
