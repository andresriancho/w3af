"""
oracle_discovery.py

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
import re

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.kb.info import Info


class oracle_discovery(CrawlPlugin):
    """
    Find Oracle applications on the remote web server.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    ORACLE_DATA = (
        # Example string:
        # <html><head><title>PPE is working</title></head><body>
        # PPE version 1.3.4 is working.</body></html>
        ('/portal/page', '<html><head><title>PPE is working</title></head>' +
                         '<body>(PPE) version (.*?) is working.</body></html>'),

        # Example strings:
        # Reports Servlet Omgevingsvariabelen 9.0.4.2.0
        # Reports Servlet Variables de Entorno 9.0.4.0.33
        ('/reports/rwservlet/showenv', '(Reports Servlet) [\w ]* ([\d\.]*)'),
    )

    ORACLE_DATA = ((url, re.compile(re_str)) for url, re_str in ORACLE_DATA)

    def __init__(self):
        CrawlPlugin.__init__(self)

    @runonce(exc_class=RunOnce)
    def crawl(self, fuzzable_request):
        """
        GET some files and parse them.

        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        base_url = fuzzable_request.get_url().base_url()

        for url, re_obj in self.ORACLE_DATA:

            oracle_discovery_URL = base_url.url_join(url)
            response = self._uri_opener.GET(oracle_discovery_URL, cache=True)

            if not is_404(response):

                # Extract the links and send to core
                for fr in self._create_fuzzable_requests(response):
                    self.output_queue.put(fr)
                
                # pylint: disable=E1101
                # E1101: Instance of 'str' has no 'search' member
                mo = re_obj.search(response.get_body(), re.DOTALL)

                if mo:
                    desc = '"%s" version "%s" was detected at "%s".'
                    desc = desc % (mo.group(1).title(), mo.group(2).title(),
                                   response.get_url())
                    i = Info('Oracle Application Server', desc, response.id,
                             self.get_name())
                    i.set_url(response.get_url())
                    
                    kb.kb.append(self, 'oracle_discovery', i)
                    om.out.information(i.get_desc())
                else:
                    msg = 'oracle_discovery found the URL: "%s" but failed to'\
                          ' parse it as an Oracle page. The first 50 bytes of'\
                          ' the response body is: "%s".'
                    body_start = response.get_body()[:50]
                    om.out.debug(msg % (response.get_url(), body_start))

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin retrieves Oracle Application Server URLs and extracts
        information available on them.
        """
