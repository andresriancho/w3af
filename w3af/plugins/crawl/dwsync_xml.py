"""
dwsync_xml.py

Copyright 2015 Andres Riancho

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

"""
import xml.dom.minidom

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.db.disk_set import DiskSet
from w3af.core.data.kb.vuln import Vuln


class dwsync_xml(CrawlPlugin):
    """
    Search Dream Waver Sync file (dwsync.xml) and extract referenced files.

    :author: Tomas Velazquez (tomas.velazquezz@gmail.com)
    """

    DWSYNC = '_notes/dwsync.xml'

    def __init__(self):
        CrawlPlugin.__init__(self)
        
        # Internal variables
        self._analyzed_dirs = DiskSet()

    def crawl(self, fuzzable_request, debugging_id):
        """
        For every directory, fetch a list of files and analyze the response.

        :param debugging_id: A unique identifier for this call to discover()
        :parameter fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        directories_to_check = []

        for domain_path in fuzzable_request.get_url().get_directories():
            if domain_path in self._analyzed_dirs:
                continue

            self._analyzed_dirs.add(domain_path)
            directories_to_check.append(domain_path)

        # Send the requests using threads
        self.worker_pool.map(self._find_dwsync, directories_to_check)

    def _find_dwsync(self, domain_path):
        dwsync_url = domain_path.url_join(self.DWSYNC)
        response = self.http_get_and_parse(dwsync_url)

        if is_404(response):
            return

        if '</dwsync>' not in response.get_body():
            return

        om.out.debug('Parsing dwsync.xml file at %s' % dwsync_url)

        try:
            dom = xml.dom.minidom.parseString(response.get_body())
        except Exception, e:
            msg = 'Exception while parsing dwsync.xml file at %s : "%s"'
            om.out.debug(msg % (dwsync_url, e))
            return

        parsed_url_list = set()

        for file_entry in dom.getElementsByTagName('file'):
            try:
                _file = file_entry.getAttribute('name')
                url = domain_path.url_join(_file)
                parsed_url_list.add(url)
            except ValueError, ve:
                msg = 'dwsync file had an invalid URL: "%s"'
                om.out.debug(msg % ve)
            except Exception, e:
                msg = 'Sitemap file had an invalid format: "%s"'
                om.out.debug(msg % e)

        if parsed_url_list:
            desc = ('A dwsync.xml file was found at: %s. The contents'
                    ' of this file disclose %s file names')
            desc %= (response.get_url(), len(parsed_url_list))

            v = Vuln('dwsync.xml file found', desc, severity.LOW,
                     response.id, self.get_name())
            v.set_url(response.get_url())

            kb.kb.append(self, 'dwsync_xml', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

            self.worker_pool.map(self.http_get_and_parse, parsed_url_list)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin searches for the "_notes/dwsync.xml" file in all
        directories and subdirectories that are sent as input, if found it
        parses the file and extracts new URLs.

        The _notes/dwsync.xml file holds  information about the list of files in
        the current directory. These files are created by Adobe Dreamweaver.

        For example, if the input is:
            - http://host.tld/w3af/index.php
            
        The plugin will perform these requests:
            - http://host.tld/w3af/_notes/dwsync.xml
            - http://host.tld/_notes/dwsync.xml
        """
