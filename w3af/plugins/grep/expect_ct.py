"""
expect_ct.py

Copyright 2019 Andres Riancho

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

ECT_HEADER = 'Expect-CT'
MAX_REPORTS = 50

class expect_ct(GrepPlugin):
    """
    Check if HTTPS responses have the Expect-CT header set.

    """
    def __init__(self):
        super(expect_ct, self).__init__()
        self._reports = 0

    def grep(self, request, response):
        """
        Check if HTTPS responses have the Expect-CT header set.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, all results are saved in the kb.
        """

        if self._reports > MAX_REPORTS:
            return
        
        
        if request.get_url().get_protocol() != 'https':
            return

        expect_ct_header_value, _ = response.get_headers().iget(ECT_HEADER, None)
        if expect_ct_header_value is not None:
            return

        self._reports += 1

        desc = 'The web server uses HTTPS but does not set the ' \
               ' Expect-CT header.'
        i = Info('Missing Expect CT header', desc,
                 response.id, self.get_name())
        i.set_url(response.get_url())
        i[ECTInfoSet.ITAG] = response.get_url().get_domain()

        self.kb_append_uniq_group(self, 'expect_ct', i,
                                  group_klass=ECTInfoSet)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Check if HTTPS responses have the Expect-CT header set
        and report missing URLs.

        https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Expect-CT
        """


class ECTInfoSet(InfoSet):
    ITAG = 'domain'
    TEMPLATE = (
        'The remote web server sent {{ uris|length }} HTTPS responses which'
        ' do not contain the Expect-CT header. The first ten'
        ' URLs which did not send the header are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )



