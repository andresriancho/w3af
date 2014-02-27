"""
strange_reason.py

Copyright 2009 Andres Riancho

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

from w3af.core.data.kb.info import Info
from w3af.core.data.constants.http_messages import W3C_REASONS
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin


class strange_reason(GrepPlugin):
    """
    Analyze HTTP response reason (Not Found, Ok, Internal Server Error).

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        GrepPlugin.__init__(self)

    def grep(self, request, response):
        """
        Plugin entry point. Analyze if the HTTP response reason messages are strange.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, all results are saved in the kb.
        """
        response_code = response.get_code()
        msg_list = W3C_REASONS.get(response_code, None)

        if msg_list is not None:

            response_reason = response.get_msg().lower()

            if response_reason not in msg_list:
                #
                #   I check if the kb already has a info object with this code:
                #
                strange_reason_infos = kb.kb.get('strange_reason',
                                                 'strange_reason')

                corresponding_info = None
                for info_obj in strange_reason_infos:
                    if info_obj['reason'] == response.get_msg():
                        corresponding_info = info_obj
                        break

                if corresponding_info:
                    # Work with the "old" info object:
                    id_list = corresponding_info.get_id()
                    id_list.append(response.id)
                    corresponding_info.set_id(id_list)

                else:
                    # Create a new info object from scratch and save it to the kb:
                    desc = 'The remote Web server sent a strange HTTP reason'\
                           'message: "%s" manual inspection is advised.'
                    desc = desc % response.get_msg()
                    i = Info('Strange HTTP Reason message', desc,
                             response.id, self.get_name())
                    i.set_url(response.get_url())
                    i['reason'] = response.get_msg()
                    i.add_to_highlight(response.get_msg())
                    
                    self.kb_append_uniq(self, 'strange_reason', i, 'URL')

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Analyze HTTP response reason messages sent by the remote web application
        and report uncommon findings.
        """
