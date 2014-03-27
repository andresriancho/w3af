"""
strange_http_codes.py

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

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.info import Info


class strange_http_codes(GrepPlugin):
    """
    Analyze HTTP response codes sent by the remote web application.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    COMMON_HTTP_CODES = set([200,
                             301, 302, 303, 304,
                             401, 403, 404,
                             500, 501])

    def __init__(self):
        GrepPlugin.__init__(self)

    def grep(self, request, response):
        """
        Plugin entry point. Analyze if the HTTP response codes are strange.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, all results are saved in the kb.
        """
        if response.get_code() in self.COMMON_HTTP_CODES:
            return

        # I check if the kb already has a info object with this code:
        strange_code_infos = kb.kb.get('strange_http_codes',
                                       'strange_http_codes')

        corresponding_info = None
        for info_obj in strange_code_infos:
            if info_obj['code'] == response.get_code():
                corresponding_info = info_obj
                break

        if corresponding_info:
            # Work with the "old" info object:
            id_list = corresponding_info.get_id()
            id_list.append(response.id)
            corresponding_info.set_id(id_list)

        else:
            # Create a new info object from scratch and save it to the kb:
            desc = 'The remote Web server sent a strange HTTP response code:'\
                   ' "%s" with the message: "%s", manual inspection is advised.'
            desc = desc % (response.get_code(), response.get_msg())
            
            i = Info('Strange HTTP response code', desc,
                     response.id, self.get_name())
            i.set_url(response.get_url())
            i['code'] = response.get_code()
            i.add_to_highlight(str(response.get_code()), response.get_msg())
            
            self.kb_append_uniq(self, 'strange_http_codes', i, 'URL')

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Analyze HTTP response codes sent by the remote web application and
        report uncommon findings.
        """
