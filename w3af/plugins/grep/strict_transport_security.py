"""
strict_transport_security.py

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

STS_HEADER = 'Strict-Transport-Security'
MAX_REPORTS = 50


class strict_transport_security(GrepPlugin):
    """
    Check if HTTPS responses have the Strict-Transport-Security header set.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        super(strict_transport_security, self).__init__()
        self._reports = 0

    def grep(self, request, response):
        """
        Check if HTTPS responses have the Strict-Transport-Security header set.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, all results are saved in the kb.
        """
        if self._reports > MAX_REPORTS:
            return

        if request.get_url().get_protocol() != 'https':
            return

        sts_header_value, _ = response.get_headers().iget(STS_HEADER, None)
        if sts_header_value is not None:
            return

        self._reports += 1

        desc = 'The web server uses HTTPS but does not set the '\
               ' Strict-Transport-Security header.'
        i = Info('Missing Strict Transport Security header', desc,
                 response.id, self.get_name())
        i.set_url(response.get_url())
        i[STSInfoSet.ITAG] = response.get_url().get_domain()

        self.kb_append_uniq_group(self, 'strict_transport_security', i,
                                  group_klass=STSInfoSet)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Check if HTTPS responses have the Strict-Transport-Security header set
        and report missing URLs.

        https://en.wikipedia.org/wiki/HTTP_Strict_Transport_Security
        """


class STSInfoSet(InfoSet):
    ITAG = 'domain'
    TEMPLATE = (
        'The remote web server sent {{ uris|length }} HTTPS responses which'
        ' do not contain the Strict-Transport-Security header. The first ten'
        ' URLs which did not send the header are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )

