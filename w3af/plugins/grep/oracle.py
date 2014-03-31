"""
oracle.py

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
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.info import Info


class oracle(GrepPlugin):
    """
    Find Oracle applications.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    OAS_TAGS = ['<!-- Created by Oracle ',]

    def __init__(self):
        GrepPlugin.__init__(self)

    def grep(self, request, response):
        """
        Plugin entry point. Grep for oracle applications.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        if not response.is_text_or_html():
            return

        for msg in self.OAS_TAGS:
            if msg in response:
                desc = 'The URL: "%s" was created using Oracle Application'\
                       ' Server.'
                desc = desc % response.get_url()
                i = Info('Oracle application server', desc, response.id,
                         self.get_name())
                i.set_url(response.get_url())
                i.add_to_highlight(msg)
                
                self.kb_append(self, 'oracle', i)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page for oracle messages, versions, etc.
        """
