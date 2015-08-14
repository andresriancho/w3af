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
from w3af.core.data.kb.info import Info
from w3af.core.data.kb.info_set import InfoSet
from w3af.core.data.constants.http_messages import W3C_REASONS
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin


class strange_reason(GrepPlugin):
    """
    Analyze HTTP response reason (Not Found, Ok, Internal Server Error).

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def grep(self, request, response):
        """
        Analyze if the HTTP response reason messages are strange.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, all results are saved in the kb.
        """
        response_code = response.get_code()
        msg_list = W3C_REASONS.get(response_code, None)

        if msg_list is None:
            return

        response_reason = response.get_msg().lower()

        if response_reason in msg_list:
            # It's common, nothing to do here.
            return

        # Create a new info object from scratch and save it to the kb:
        desc = ('The remote Web server sent a strange HTTP reason'
                ' message "%s", manual inspection is recommended.')
        desc %= response.get_msg()

        i = Info('Strange HTTP Reason message',
                 desc, response.id, self.get_name())
        i.set_url(response.get_url())
        i.add_to_highlight(response.get_msg())
        i[StrangeHeaderInfoSet.ITAG] = response.get_msg()

        self.kb_append_uniq_group(self, 'strange_reason', i,
                                  group_klass=StrangeHeaderInfoSet)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Analyze HTTP response reason messages sent by the remote web application
        and report uncommon findings.
        """


class StrangeHeaderInfoSet(InfoSet):
    ITAG = 'reason'
    TEMPLATE = (
        'The remote web server sent {{ uris|length }} HTTP responses with'
        ' the uncommon status message "{{ reason }}", manual inspection is'
        ' recommended. The first ten URLs which sent the uncommon message'
        ' are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )