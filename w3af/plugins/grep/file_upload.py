"""
file_upload.py

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


class file_upload(GrepPlugin):
    """
    Find HTML forms with file upload capabilities.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def grep(self, request, response):
        """
        Plugin entry point, verify if the HTML has a form with file uploads.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        if not response.is_text_or_html():
            return
        
        for tag in parser_cache.dpc.get_tags_by_filter(response, ('input',)):
            # pylint: disable=E1101
            input_type = tag.attrib.get('type', None)
            # pylint: enable=E1101

            if input_type is None:
                continue

            if input_type.lower() != 'file':
                continue

            url = response.get_url()

            msg = 'A form which allows file uploads was found at "%s"'
            msg %= url

            i = Info('File upload form', msg, response.id, self.get_name())
            i.set_url(url)

            self.kb_append_uniq(self, 'file_upload', i, 'URL')
            break

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin identifies URLs which contain forms that allow file uploads.
        """
