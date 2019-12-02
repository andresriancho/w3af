"""
favicon_identification.py

Copyright 2009 Vlatko Kosturjak
Plugin based on wordpress_fingerprint.py and pykto.py

More information to be found here:
    http://www.owasp.org/index.php/Category:OWASP_Favicon_Database_Project
    http://kost.com.hr/favicon.php

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
import hashlib
import os.path

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af import ROOT_PATH
from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.data.kb.info import Info


class favicon_identification(InfrastructurePlugin):
    """
    Identify server software using favicon.
    :author: Vlatko Kosturjak  <kost@linux.hr> http://kost.com.hr
    """

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        # Internal variables
        self._version = None

        # User configured parameters
        self._db_file = os.path.join(ROOT_PATH, 'plugins', 'infrastructure',
                                     'favicon', 'favicon-md5')

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        Identify server software using favicon.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                (among other things) the URL to test.
        """
        domain_path = fuzzable_request.get_url().get_domain_path()

        # TODO: Maybe I should also parse the html to extract the favicon location?
        favicon_url = domain_path.url_join('favicon.ico')
        response = self._uri_opener.GET(favicon_url, cache=True)
        remote_fav_md5 = hashlib.md5(response.get_body()).hexdigest()

        if not is_404(response):

            # check if MD5 is matched in database/list
            for md5part, favicon_desc in self._read_favicon_db():

                if md5part == remote_fav_md5:
                    desc = 'Favicon.ico file was identified as "%s".' % favicon_desc
                    i = Info('Favicon identification', desc, response.id,
                             self.get_name())
                    i.set_url(favicon_url)
                    
                    kb.kb.append(self, 'info', i)
                    om.out.information(i.get_desc())
                    break
            else:
                #
                #   Report to the kb that we failed to ID this favicon.ico
                #   and that the md5 should be sent to the developers.
                #
                desc = 'Favicon identification failed. If the remote site is'  \
                       ' using framework that is being exposed by its favicon,'\
                       ' please send an email to w3af-develop@lists.sourceforge.net'\
                       ' including this md5 hash "%s" and the' \
                       ' name of the server or Web application it represents.' \
                       ' New fingerprints make this plugin more powerful and ' \
                       ' accurate.'
                desc = desc % remote_fav_md5
                i = Info('Favicon identification failed', desc, response.id,
                         self.get_name())
                i.set_url(favicon_url)

                kb.kb.append(self, 'info', i)
                om.out.information(i.get_desc())

    def _read_favicon_db(self):
        try:
            # read MD5 database.
            db_file = open(self._db_file, "r")
        except Exception, e:
            msg = 'Failed to open the MD5 database at %s. Exception: "%s".'
            om.out.error(msg % (self._db_file, e))
        else:
            for line in db_file:
                line = line.strip()
                md5part, favicon_desc = line.split(":", 1)
                yield md5part, favicon_desc

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin identifies software version using favicon.ico file.

        It checks MD5 of favicon against the MD5 database of favicons. See also:
            http://www.owasp.org/index.php/Category:OWASP_Favicon_Database_Project
            http://kost.com.hr/favicon.php
        """
