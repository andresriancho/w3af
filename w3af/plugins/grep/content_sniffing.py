"""
content_sniffing.py

Copyright 2015 Andres Riancho

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
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin

CT_OPTIONS_HEADER = 'X-Content-Type-Options'
NOSNIFF = 'nosniff'
MAX_REPORTS = 50


class content_sniffing(GrepPlugin):
    """
    Check if all responses have X-Content-Type-Options header set

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        super(content_sniffing, self).__init__()
        self._reports = 0

    def grep(self, request, response):
        """
        Check if all responses have X-Content-Type-Options header set

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, all results are saved in the kb.
        """
        if self._reports > MAX_REPORTS:
            return

        ct_options_value, _ = response.get_headers().iget(CT_OPTIONS_HEADER, None)
        if ct_options_value is not None:
            if ct_options_value.strip().lower() == NOSNIFF:
                return

        self._reports += 1

        desc = ('The URL "%s" returned an HTTP response without the'
                ' recommended HTTP header X-Content-Type-Options')
        desc %= response.get_url()

        i = Info('Missing X-Content-Type-Options header', desc,
                 response.id, self.get_name())
        i.set_url(response.get_url())
        i[CTSniffingInfoSet.ITAG] = response.get_url().get_domain()

        self.kb_append_uniq_group(self, 'content_sniffing', i,
                                  group_klass=CTSniffingInfoSet)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Check if all responses have X-Content-Type-Options header set.
        """


class CTSniffingInfoSet(InfoSet):
    ITAG = 'domain'
    TEMPLATE = (
        'The remote web application sent {{ uris|length }} HTTP responses'
        ' which do not contain the X-Content-Type-Options header. The first'
        ' ten URLs which did not send the header are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )

