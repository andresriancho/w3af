"""
ds_store.py

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
import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.db.disk_set import DiskSet
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.parsers.doc.ds_store_parser import DSStoreParser


class ds_store(CrawlPlugin):
    """
    Search .DS_Store file and checks for files containing.

    :author: Tomas Velazquez (tomas.velazquezz@gmail.com)
    """

    DS_STORE = '.DS_Store'

    def __init__(self):
        CrawlPlugin.__init__(self)
        self._analyzed_dirs = DiskSet()

    def crawl(self, fuzzable_request):
        """
        For every directory, fetch a list of files and analyze the response.

        :parameter fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        for domain_path in fuzzable_request.get_url().get_directories():
            if domain_path not in self._analyzed_dirs:
                self._analyzed_dirs.add(domain_path)
                self._check_and_analyze(domain_path)

    def _check_and_analyze(self, domain_path):
        """
        Check if a .DS_Store filename exists in the domain_path.
        :return: None, everything is saved to the self.out_queue.
        """
        url = domain_path.url_join(self.DS_STORE)

        try:
            response = self.http_get_and_parse(url)
        except BaseFrameworkException, e:
            msg = 'Failed to GET .DS_Store URL at "%s". Exception: "%s".'
            om.out.debug(msg, (url, e))
            return

        if is_404(response):
            return

        if not DSStoreParser.can_parse(response):
            return

        parser = DSStoreParser(response)
        parser.parse()
        references, _ = parser.get_references()

        self.worker_pool.map(self.http_get_and_parse, references)

        if references:
            desc = ('A .DS_Store file was found at: "%s". The contents'
                    ' of this file discloses %s filenames')
            desc %= (response.get_url(), len(references))

            v = Vuln('.DS_Store file found', desc, severity.LOW, response.id,
                     self.get_name())
            v.set_url(response.get_url())

            kb.kb.append(self, 'ds_store', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin searches for the .DS_Store file in all directories and
        subdirectories that are sent as input and if found extracts new URLs
        from it's content.

        The .DS_Store file holds information about the list of files in the
        current directory. These files are created by the Mac OS X Finder in
        every directory that it accesses.

        For example, if the plugin input URL is:
            - http://host.tld/w3af/index.php

        The plugin will perform these requests:
            - http://host.tld/w3af/.DS_Store
            - http://host.tld/.DS_Store
        """
