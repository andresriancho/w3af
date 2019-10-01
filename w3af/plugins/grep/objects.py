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
import w3af.core.data.parsers.parser_cache as parser_cache

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.info import Info


class objects(GrepPlugin):
    """
    Grep every page for objects and applets.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    TAGS = ('object', 'applet')

    def grep(self, request, response):
        """
        Plugin entry point. Parse the object tags.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        if not response.is_text_or_html():
            return

        url = response.get_url()

        for tag in parser_cache.dpc.get_tags_by_filter(response, self.TAGS):
            # pylint: disable=E1101
            desc = ('The URL: "%s" has an "%s" tag. We recommend you download'
                    ' the client side code and analyze it manually.')
            desc %= (response.get_uri(), tag.name)

            i = Info('Browser plugin content', desc, response.id,
                     self.get_name())
            i.set_url(url)
            i.add_to_highlight('<%s' % tag.name)

            self.kb_append_uniq(self, tag.name, i, 'URL')
            # pylint: enable=E1101

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page for applets and other types of objects.
        """
