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
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.info import Info
from w3af.core.data.kb.info_set import InfoSet


class strange_http_codes(GrepPlugin):
    """
    Analyze HTTP response codes sent by the remote web application.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    COMMON_HTTP_CODES = {200, 301, 302, 303, 304, 308, 401, 403, 404, 500, 501}

    # https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#5xx_Server_errors
    DOS_HTTP_CODES = {502, 503, 504, 508, 509, 530, 598, 520, 521, 522, 523,
                      524, 525, 527}

    def grep(self, request, response):
        """
        Plugin entry point. Analyze if the HTTP response codes are strange.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, all results are saved in the kb.
        """
        if response.get_code() in self.COMMON_HTTP_CODES:
            return

        identified_http_code = self._identify_and_report(request, response)

        if not identified_http_code:
            self._report_generic(request, response)

    def _identify_and_report(self, request, response):
        """
        Use the list from:

            https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#5xx_Server_errors

        To identify specific response codes and report them. These reports
        are actionable since they might include information about the scan
        triggering a DoS (or similar) situation.

        :param request: HTTP request
        :param response: HTTP response
        :return: True if the method was able to identify a specific "strange"
                 HTTP response code.
        """
        if response.get_code() not in self.DOS_HTTP_CODES:
            return False

        desc = ('The remote web server sent an HTTP response code: "%s" with'
                ' the message: "%s", this is usually associated with the server'
                ' being under heavy load. The scan results might be inaccurate'
                ' if many of these HTTP responses are found.')
        desc %= (response.get_code(), response.get_msg())

        i = Info('Server under heavy load', desc, response.id, self.get_name())
        i.add_to_highlight(str(response.get_code()), response.get_msg())
        i.set_url(response.get_url())
        i[HeavyLoadCodesInfoSet.ITAG] = response.get_code()
        i['message'] = response.get_msg()

        self.kb_append_uniq_group(self, 'heavy_load', i,
                                  group_klass=HeavyLoadCodesInfoSet)

        return True

    def _report_generic(self, request, response):
        """
        When we were unable to identify any specific "strange" HTTP response
        codes we call this method to report the generic ones.

        :param request: HTTP request
        :param response: HTTP response
        :return: None, we save the information to the KB
        """
        # Create a new info object from scratch and save it to the kb
        desc = ('The remote Web server sent a strange HTTP response code:'
                ' "%s" with the message: "%s", manual inspection is'
                ' recommended.')
        desc %= (response.get_code(), response.get_msg())

        i = Info('Strange HTTP response code',
                 desc, response.id, self.get_name())
        i.add_to_highlight(str(response.get_code()), response.get_msg())
        i.set_url(response.get_url())
        i[StrangeCodesInfoSet.ITAG] = response.get_code()
        i['message'] = response.get_msg()

        self.kb_append_uniq_group(self, 'strange_http_codes', i,
                                  group_klass=StrangeCodesInfoSet)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Analyze HTTP response codes sent by the remote web application and
        report uncommon findings.
        """


class StrangeCodesInfoSet(InfoSet):
    ITAG = 'code'
    TEMPLATE = (
        'The remote web server sent {{ uris|length }} HTTP responses with'
        ' the uncommon response status code {{ code }} using "{{ message }}"'
        ' as message. The first ten URLs which sent the uncommon status code'
        ' are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )


class HeavyLoadCodesInfoSet(InfoSet):
    ITAG = 'code'
    TEMPLATE = (
        'The remote web server sent {{ uris|length }} HTTP responses with'
        ' the uncommon response status code {{ code }} using "{{ message }}"'
        ' as message. '
        ''
        'This HTTP response code is usually associated with the server being'
        ' under heavy load. The scan results might be inaccurate if many of'
        ' these HTTP responses are found.'
        ''
        'The first ten URLs which sent the uncommon status code are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )
