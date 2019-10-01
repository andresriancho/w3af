"""
ds_store.py

Copyright 2013 Tomas Velazquez

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
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from ds_store import DSStore

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.db.disk_set import DiskSet
from w3af.core.data.kb.vuln import Vuln


class dot_ds_store(CrawlPlugin):
    """
    Search .DS_Store file and checks for files containing.

    :author: Tomas Velazquez ( tomas.velazquezz@gmail.com )
    :author: Andres Riancho ( andres.riancho@gmail.com )

    :credits: This code was based in cpan Mac::Finder::DSStore by Wim Lewis ( wiml@hhhh.org )
    """
    DS_STORE = '.DS_Store'

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
            if domain_path not in self._analyzed_dirs:
                self._analyzed_dirs.add(domain_path)
                directories_to_check.append(domain_path)

        # Send the requests using threads
        self.worker_pool.map(self._check_and_analyze, directories_to_check)

    def _check_and_analyze(self, domain_path):
        """
        Check if a .DS_Store filename exists in the domain_path.

        :return: None, everything is saved to the self.out_queue.
        """
        # Request the file
        url = domain_path.url_join(self.DS_STORE)

        try:
            response = self.http_get_and_parse(url, binary_response=True)
        except BaseFrameworkException, w3:
            msg = 'Failed to GET .DS_Store file: %s. Exception: %s.'
            om.out.debug(msg, (url, w3))
            return

        # Check if it's a .DS_Store file
        if is_404(response):
            return

        try:
            store = DsStore(response.get_raw_body())
            entries = store.get_file_entries()
        except Exception, e:
            om.out.debug('Unexpected error while parsing DS_Store file: "%s"' % e)
            return

        parsed_url_list = []

        for filename in entries:
            parsed_url_list.append(domain_path.url_join(filename))

        self.worker_pool.map(self.http_get_and_parse, parsed_url_list)

        desc = ('A .DS_Store file was found at: %s. The contents of this file'
                ' disclose filenames')
        desc %= (response.get_url())

        v = Vuln('.DS_Store file found', desc, severity.LOW, response.id, self.get_name())
        v.set_url(response.get_url())

        kb.kb.append(self, 'dot_ds_store', v)
        om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return '''
        This plugin searches for the .DS_Store file in all the directories and
        subdirectories that are sent as input. If the file is found extract new
        URLs from its content.
        
        The .DS_Store file holds information about the list of files in the 
        current directory. These files are created by the Mac OS X Finder in every
        directory that it accesses.
        
        For example, if the plugin input is:
            - http://host.tld/w3af/index.php

        The plugin will perform these requests:
            - http://host.tld/w3af/.DS_Store
            - http://host.tld/.DS_Store
        '''


class DsStore(object):

    def __init__(self, data):
        self._store = None
        self.init(data)

    def init(self, data):
        """
        Open a .DS_Store file
        """
        _input = StringIO(data)
        self._store = DSStore.open(_input)

    def get_file_entries(self):
        entries = set()

        for data in self._store:
            data = str(data)
            entry = data.translate(None, "<>")
            entry = entry.split(' ')

            filename = entry[0]
            if filename in ('.', '..'):
                continue

            entries.add(filename)

        return entries
