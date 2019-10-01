"""
finger_pks.py

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
import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.data.search_engines.pks import pks
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.kb.info import Info


class finger_pks(InfrastructurePlugin):
    """
    Search MIT PKS to get a list of users for a domain.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        root_domain = fuzzable_request.get_url().get_root_domain()

        pks_se = pks(self._uri_opener)
        results = pks_se.search(root_domain)
        pks_url = 'http://pgp.mit.edu:11371/'

        for result in results:
            mail = result.username + '@' + root_domain
            
            desc = 'The mail account: "%s" was found at: "%s".'
            desc %= (mail, pks_url)

            i = Info('Email account', desc, result.id, self.get_name())
            i.set_url(URL(pks_url))
            i['mail'] = mail
            i['user'] = result.username
            i['name'] = result.name
            i['url_list'] = {URL(pks_url)}
            
            kb.kb.append('emails', 'emails', i)
            om.out.information(i.get_desc())

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds mail addresses in PGP PKS servers.
        """
