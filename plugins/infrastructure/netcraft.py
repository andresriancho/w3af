'''
netcraft.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
import re

import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb

from core.controllers.misc.decorators import runonce
from core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from core.controllers.exceptions import w3afException, w3afRunOnce

from core.data.kb.info import Info
from core.data.parsers.url import URL


class netcraft(InfrastructurePlugin):
    '''
    Find out "What's that site running?".

    @author: ino ( guerrino.dimassa@gmail.com )
    '''
    def __init__(self):
        InfrastructurePlugin.__init__(self)

    @runonce(exc_class=w3afRunOnce)
    def discover(self, fuzzable_request):
        '''
        Search netcraft and parse the output.

        @param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the site to test.
        '''
        target_domain = fuzzable_request.get_url().get_root_domain()

        # Example URL:
        # http://toolbar.netcraft.com/site_report?url=http://www.foo.org
        #

        nc_url_str = 'http://toolbar.netcraft.com/site_report?url=' + \
            target_domain
        nc_url = URL(nc_url_str)

        try:
            response = self._uri_opener.GET(nc_url)
        except w3afException, e:
            msg = 'An exception was raised while running netcraft plugin. Exception: ' + str(e)
            om.out.debug(msg)
        else:
            self._parse_netcraft(response)

    def _parse_netcraft(self, response):
        '''
        Parses netcraft's response and stores information in the KB

        @param response: The http response object from querying netcraft
        @return: None, data stored in KB.
        '''

        # Netblock owner:
        #
        # Example: <td><b>Netblock owner</b></td><td width=38%>
        #          <a href="/netblock?q=GO-DADDY-COM-LLC,64.202.160.0,64.202.191.255">
        #          GoDaddy.com, LLC</a></td>
        #
        # (all in the same line)
        re_netblock = '<td><b>Netblock owner</b></td><td width=38%><a href=".*?">(.*?)</a></td>'
        netblock_owner_match = re.search(re_netblock, response.body)

        if netblock_owner_match:
            netblock_owner = netblock_owner_match.group(1)

            desc = 'Netcraft reports that the netblock owner for the target'\
                   ' domain is %s.'
            desc = desc % netblock_owner

            i = Info('Netblock owner', desc, response.id, self.get_name())

            # Save the results in the KB so the user can look at it
            kb.kb.append(self, 'netblock_owner', i)

    def get_long_desc(self):
        return '''
        This plugin searches the netcraft database and parses the result. The
        information stored in that database is useful to know about Netblock
        Owner,IP address,OS,Web Server,Last changed of the site.
        '''
