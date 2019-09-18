"""
dot_listing.py

Copyright 2012 Tomas Velazquez

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

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class dot_listing(CrawlPlugin):
    """
    Search for .listing files and extracts new filenames from it.
    :author: Tomas Velazquez ( tomas.velazquezz@gmail.com )
    """
    # -rw-r--r--    1 andresr   w3af         8139 Apr 12 13:23 foo.zip
    regex_str = r'[a-z-]{10}\s*\d+\s*(.*?)\s+(.*?)\s+\d+\s+\w+\s+\d+\s+[0-9:]{4,5}\s+(.*)'
    LISTING_PARSER_RE = re.compile(regex_str)
    
    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._analyzed_dirs = ScalableBloomFilter()

    def crawl(self, fuzzable_request, debugging_id):
        """
        For every directory, fetch the .listing file and analyze the response.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        directories_to_check = []

        for domain_path in fuzzable_request.get_url().get_directories():
            if domain_path in self._analyzed_dirs:
                continue

            self._analyzed_dirs.add(domain_path)
            directories_to_check.append(domain_path)

        # Send the requests using threads
        self.worker_pool.map(self._check_and_analyze, directories_to_check)

    def _check_and_analyze(self, domain_path):
        """
        Check if a .listing filename exists in the domain_path.
        :return: None, everything is saved to the self.out_queue.
        """
        url = domain_path.url_join('.listing')
        response = self._uri_opener.GET(url, cache=True)

        if is_404(response):
            return

        parsed_url_set = set()
        users = set()
        groups = set()

        # Check if it's a .listing file
        extracted_info = self._extract_info_from_listing(response.get_body())
        for username, group, filename in extracted_info:
            if filename in ('.', '..'):
                continue

            parsed_url_set.add(domain_path.url_join(filename))
            users.add(username)
            groups.add(group)

        self.worker_pool.map(self.http_get_and_parse, parsed_url_set)

        if parsed_url_set:
            desc = ('A .listing file was found at: "%s". The contents'
                    ' of this file disclose filenames.')
            desc %= (response.get_url())

            v = Vuln('.listing file found', desc, severity.LOW, response.id,
                     self.get_name())
            v.set_url(response.get_url())

            kb.kb.append(self, 'dot_listing', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

            fr = FuzzableRequest(response.get_url())
            self.output_queue.put(fr)

        real_users = set([u for u in users if not u.isdigit()])
        real_groups = set([g for g in groups if not g.isdigit()])

        if real_users or real_groups:
            desc = ('A .listing file which leaks operating system user names'
                    ' and groups was identified at %s. The leaked users are %s,'
                    ' and the groups are %s. This information can be used'
                    ' during a bruteforce attack of the Web application,'
                    ' SSH or FTP services.')
            desc %= (response.get_url(),
                     ', '.join(real_users),
                     ', '.join(real_groups))

            v = Vuln('Operating system username and group leak', desc,
                     severity.LOW, response.id, self.get_name())
            v.set_url(response.get_url())

            kb.kb.append(self, 'dot_listing', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _extract_info_from_listing(self, listing_file_content):
        """
        Extract info from .listing file content, each line looks like:

        -rw-r--r--    1 andresr   w3af         8139 Apr 12 13:23 foo.zip

        We're going to extract "andresr" (user), "w3af" (group) and "foo.zip"
        (file).

        :return: A list with the information extracted from the listing_file_content
        """
        for user, group, filename in self.LISTING_PARSER_RE.findall(listing_file_content):
            yield user, group, filename.strip()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin searches for the .listing file in all the directories and
        subdirectories that are sent as input. If the file is found extract new
        URLs from its content.
        
        The .listing file holds information about the list of files in the current
        directory. These files are created when download files from FTP with command
        "wget" and argument "-m" or "--no-remove-listing".
        
        For example, if the input is:
            - http://host.tld/w3af/index.php

        The plugin will perform these requests:
            - http://host.tld/w3af/.listing
            - http://host.tld/.listing
        """
