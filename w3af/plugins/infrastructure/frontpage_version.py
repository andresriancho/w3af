"""
frontpage_version.py

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

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.misc.decorators import runonce

from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.info import Info
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class frontpage_version(InfrastructurePlugin):
    """
    Search FrontPage Server Info file and if it finds it will determine its version.
    :author: Viktor Gazdag ( woodspeed@gmail.com )
    """
    VERSION_RE = re.compile('FPVersion="(.*?)"', re.IGNORECASE)
    ADMIN_URL_RE = re.compile('FPAdminScriptUrl="(.*?)"', re.IGNORECASE)
    AUTHOR_URL_RE = re.compile('FPAuthorScriptUrl="(.*?)"', re.IGNORECASE)

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        # Internal variables
        self._analyzed_dirs = ScalableBloomFilter()

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request, debugging_id):
        """
        For every directory, fetch a list of files and analyze the response.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        for domain_path in fuzzable_request.get_url().get_directories():

            if domain_path in self._analyzed_dirs:
                continue

            # Save the domain_path so I know I'm not working in vane
            self._analyzed_dirs.add(domain_path)

            # Request the file
            frontpage_info_url = domain_path.url_join("_vti_inf.html")
            try:
                response = self._uri_opener.GET(frontpage_info_url,
                                                cache=True)
            except BaseFrameworkException, w3:
                fmt = ('Failed to GET Frontpage Server _vti_inf.html file: "%s". '
                       'Exception: "%s".')
                om.out.debug(fmt % (frontpage_info_url, w3))
            else:
                # Check if it's a Frontpage Info file
                if not is_404(response):
                    fr = FuzzableRequest(response.get_uri())
                    self.output_queue.put(fr)

                    self._analyze_response(response)

    def _analyze_response(self, response):
        """
        It seems that we have found a _vti_inf file, parse it and analyze the
        content!

        :param response: The http response object for the _vti_inf file.
        :return: None. All the info is saved to the kb.
        """
        version_mo = self.VERSION_RE.search(response.get_body())
        admin_mo = self.ADMIN_URL_RE.search(response.get_body())
        author_mo = self.AUTHOR_URL_RE.search(response.get_body())

        if version_mo and admin_mo and author_mo:
            self._exec = False

            desc = ('The FrontPage Configuration Information file was found'
                    ' at: "%s" and the version of FrontPage Server Extensions'
                    ' is: "%s".')
            desc %= (response.get_url(), version_mo.group(1))

            i = Info('FrontPage configuration information', desc, response.id,
                     self.get_name())
            i.set_url(response.get_url())
            i['version'] = version_mo.group(1)
            
            kb.kb.append(self, 'frontpage_version', i)
            om.out.information(i.get_desc())

            #
            # Handle the admin.exe file
            #
            self._analyze_admin(response, admin_mo)

            #
            # Handle the author.exe file
            #
            self._analyze_author(response, author_mo)

        else:
            # This is strange... we found a _vti_inf file, but there is no
            # frontpage information in it... IPS? WAF? honeypot?
            msg = '[IMPROVEMENT] Invalid frontPage configuration information'\
                  ' found at %s (id: %s).'
            msg = msg % (response.get_url(), response.id)
            om.out.debug(msg)

    def _analyze_admin(self, response, frontpage_admin):
        """
        Analyze the admin URL.

        :param response: The http response object for the _vti_inf file.
        :param frontpage_admin: A regex match object.
        :return: None. All the info is saved to the kb.
        """
        admin_location = response.get_url().get_domain_path().url_join(
            frontpage_admin.group(1))
        
        # Check for anomalies in the location of admin.exe
        if frontpage_admin.group(1) != '_vti_bin/_vti_adm/admin.exe':
            name = 'Customized frontpage configuration'
            
            desc = 'The FPAdminScriptUrl is at: "%s" instead of the default'\
                   ' location "_vti_bin/_vti_adm/admin.exe". This is very'\
                   ' uncommon.'
            desc = desc % admin_location
            
        else:
            name = 'FrontPage FPAdminScriptUrl'

            desc = 'The FPAdminScriptUrl is at: "%s".'
            desc = desc % admin_location

        i = Info(name, desc, response.id, self.get_name())
        i.set_url(admin_location)
        i['FPAdminScriptUrl'] = admin_location
        
        kb.kb.append(self, 'frontpage_version', i)
        om.out.information(i.get_desc())

    def _analyze_author(self, response, frontpage_author):
        """
        Analyze the author URL.

        :param response: The http response object for the _vti_inf file.
        :param frontpage_author: A regex match object.
        :return: None. All the info is saved to the kb.
        """
        domain_path = response.get_url().get_domain_path()
        author_location = domain_path.url_join(frontpage_author.group(1))

        # Check for anomalies in the location of author.exe
        if frontpage_author.group(1) != '_vti_bin/_vti_aut/author.exe':
            name = 'Customized frontpage configuration'

            desc = ('The FPAuthorScriptUrl is at: "%s" instead of the default'
                    ' location: "/_vti_bin/_vti_adm/author.exe". This is very'
                    ' uncommon.')
            desc %= author_location
        else:
            name = 'FrontPage FPAuthorScriptUrl'

            desc = 'The FPAuthorScriptUrl is at: "%s".'
            desc %= author_location

        i = Info(name, desc, response.id, self.get_name())
        i.set_url(author_location)
        i['FPAuthorScriptUrl'] = author_location
        
        kb.kb.append(self, 'frontpage_version', i)
        om.out.information(i.get_desc())

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin searches for the FrontPage Server Info file and if it finds
        it will try to determine the version of the Frontpage Server Extensions.
        The file is located inside the web server webroot. For example:

            - http://localhost/_vti_inf.html
        """
