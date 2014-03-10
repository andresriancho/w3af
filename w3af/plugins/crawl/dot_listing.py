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
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.vuln import Vuln


class dot_listing(CrawlPlugin):
    """
    Search for .listing files and extracts new filenames from it.
    :author: Tomas Velazquez ( tomas.velazquezz@gmail.com )
    """

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._analyzed_dirs = ScalableBloomFilter()

        # -rw-r--r--    1 andresr   w3af         8139 Apr 12 13:23 foo.zip
        regex_str = '[a-z-]{10}\s*\d+\s*(.*?)\s+(.*?)\s+\d+\s+\w+\s+\d+\s+[0-9:]{4,5}\s+(.*)'
        self._listing_parser_re = re.compile(regex_str)

    def crawl(self, fuzzable_request):
        """
        For every directory, fetch the .listing file and analyze the response.

        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        for domain_path in fuzzable_request.get_url().get_directories():
            if domain_path not in self._analyzed_dirs:
                self._analyzed_dirs.add(domain_path)
                self._check_and_analyze(domain_path)

    def _check_and_analyze(self, domain_path):
        """
        Check if a .listing filename exists in the domain_path.
        :return: None, everything is saved to the self.out_queue.
        """
        # Request the file
        url = domain_path.url_join('.listing')
        try:
            response = self._uri_opener.GET(url, cache=True)
        except BaseFrameworkException, w3:
            msg = ('Failed to GET .listing file: "%s". Exception: "%s".')
            om.out.debug(msg % (url, w3))
            return

        # Check if it's a .listing file
        if not is_404(response):

            for fr in self._create_fuzzable_requests(response):
                self.output_queue.put(fr)

            parsed_url_set = set()
            users = set()
            groups = set()

            extracted_info = self._extract_info_from_listing(response.get_body())
            for username, group, filename in extracted_info:
                if filename != '.' and filename != '..':
                    parsed_url_set.add(domain_path.url_join(filename))
                    users.add(username)
                    groups.add(group)

            self.worker_pool.map(self.http_get_and_parse, parsed_url_set)

            if parsed_url_set:
                desc = 'A .listing file was found at: "%s". The contents'\
                       ' of this file disclose filenames.'
                desc = desc % (response.get_url())
                
                v = Vuln('.listing file found', desc, severity.LOW,
                         response.id, self.get_name())
                v.set_url(response.get_url())
                
                kb.kb.append(self, 'dot_listing', v)
                om.out.vulnerability(v.get_desc(),
                                     severity=v.get_severity())

            real_users = set([u for u in users if not u.isdigit()])
            real_groups = set([g for g in groups if not g.isdigit()])

            if real_users or real_groups:
                desc = 'A .listing file which leaks operating system usernames' \
                       ' and groups was identified at %s. The leaked users are %s,' \
                       ' and the groups are %s. This information can be used' \
                       ' during a bruteforce attack to the Web application,' \
                       ' SSH or FTP services.'
                desc = desc % (v.get_url(),
                               ', '.join(real_users),
                               ', '.join(real_groups))
                
                v = Vuln('Operating system username and group leak', desc, severity.LOW,
                         response.id, self.get_name())
                v.set_url(response.get_url())
                
                kb.kb.append(self, 'dot_listing', v)
                om.out.vulnerability(v.get_desc(),
                                     severity=v.get_severity())

    def _extract_info_from_listing(self, listing_file_content):
        """
        Extract info from .listing file content, each line looks like:

        -rw-r--r--    1 andresr   w3af         8139 Apr 12 13:23 foo.zip

        We're going to extract "andresr" (user), "w3af" (group) and "foo.zip"
        (file).

        :return: A list with the information extracted from the listing_file_content
        """
        for user, group, filename in self._listing_parser_re.findall(listing_file_content):
            yield user, group, filename.strip()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin searches for the .listing file in all the directories and
        subdirectories that are sent as input and if found it will try to
        discover new URLs from its content. The .listing file holds information
        about the list of files in the current directory. These files are created
        when download files from FTP with command "wget" and argument "-m" or
        "--no-remove-listing". For example, if the input is:
            - http://host.tld/w3af/index.php

        The plugin will perform these requests:
            - http://host.tld/w3af/.listing
            - http://host.tld/.listing

        """
