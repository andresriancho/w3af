"""
zone_h.py

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

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity
from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import RunOnce, BaseFrameworkException
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info import Info


class zone_h(InfrastructurePlugin):
    """
    Find out if the site was defaced in the past.

    :author: Jordan Santarsieri ( jsantarsieri@cybsec.com )
    """

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        Search zone_h and parse the output.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        target_domain = fuzzable_request.get_url().get_root_domain()

        # Example URL:
        # http://www.zone-h.org/archive/domain=cyprus-stones.com

        # TODO: Keep this URL updated!
        zone_h_url_str = 'http://www.zone-h.org/archive/domain=%s' % target_domain
        zone_h_url = URL(zone_h_url_str)

        try:
            response = self._uri_opener.GET(zone_h_url)
        except BaseFrameworkException, e:
            msg = 'An exception was raised while running zone-h plugin.'
            msg += ' Exception: "%s"' % e
            om.out.debug(msg)
        else:
            self._parse_zone_h_result(response)

    def _parse_zone_h_result(self, response):
        """
        Parse the result from the zone_h site and create the corresponding info
        objects.

        :return: None
        """
        #
        #   I'm going to do only one big "if":
        #
        #       - The target site was hacked more than one time
        #       - The target site was hacked only one time
        #

        # This is the string I have to parse:
        # in the zone_h response, they are two like this, the first has to be ignored!
        regex = 'Total notifications: <b>(\d*)</b> of which <b>(\d*)</b> single ip and <b>(\d*)</b> mass'
        regex_result = re.findall(regex, response.get_body())

        try:
            total_attacks = int(regex_result[0][0])
        except IndexError:
            om.out.debug('An error was generated during the parsing of the zone_h website.')
        else:

            # Do the if...
            if total_attacks > 1:
                desc = 'The target site was defaced more than one time in the'\
                       ' past. For more information please visit the following'\
                       ' URL: "%s".' % response.get_url()
                       
                v = Vuln('Previous defacements', desc,
                         severity.MEDIUM, response.id, self.get_name())
                v.set_url(response.get_url())
                
                kb.kb.append(self, 'defacements', v)
                om.out.information(v.get_desc())
            elif total_attacks == 1:
                desc = 'The target site was defaced in the past. For more'\
                       ' information please visit the following URL: "%s".'
                desc = desc % response.get_url()
                i = Info('Previous defacements', desc, response.id,
                         self.get_name())
                i.set_url(response.get_url())

                kb.kb.append(self, 'defacements', i)
                om.out.information(i.get_desc())

    def get_long_desc(self):
        return """
        This plugin searches the zone-h.org defacement database and parses the
        result. The information stored in that database is useful to know about
        previous defacements to the target website. In some cases, the defacement
        site provides information about the exploited vulnerability, which may
        be still exploitable.
        """
