"""
find_dvcs.py

Copyright 2011 Adam Baldwin

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
import struct

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.vuln import Vuln


class find_dvcs(CrawlPlugin):
    """
    Search Git, Mercurial (HG), Bazaar (BZR), Subversion (SVN) and CVS
    repositories and checks for files containing

    :author: Adam Baldwin (adam_baldwin@ngenuity-is.com)
    :author: Tomas Velazquez (tomas.velazquezz - gmail.com)
    """

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._analyzed_dirs = ScalableBloomFilter()
        self._analyzed_filenames = ScalableBloomFilter()

        self._dvcs = {'git repository': {},
                      'git ignore': {},
                      'hg repository': {},
                      'hg ignore': {},
                      'bzr repository': {},
                      'bzr ignore': {},
                      'svn repository': {},
                      'svn ignore': {},
                      'cvs repository': {},
                      'cvs ignore': {}}

        self._dvcs['git repository']['filename'] = '.git/index'
        self._dvcs['git repository']['function'] = self.git_index

        self._dvcs['git ignore']['filename'] = '.gitignore'
        self._dvcs['git ignore']['function'] = self.ignore_file

        self._dvcs['hg repository']['filename'] = '.hg/dirstate'
        self._dvcs['hg repository']['function'] = self.hg_dirstate

        self._dvcs['hg ignore']['filename'] = '.hgignore'
        self._dvcs['hg ignore']['function'] = self.ignore_file

        self._dvcs['bzr repository']['filename'] = '.bzr/checkout/dirstate'
        self._dvcs['bzr repository']['function'] = self.bzr_checkout_dirstate

        self._dvcs['bzr ignore']['filename'] = '.bzrignore'
        self._dvcs['bzr ignore']['function'] = self.ignore_file

        self._dvcs['svn repository']['filename'] = '.svn/entries'
        self._dvcs['svn repository']['function'] = self.svn_entries

        self._dvcs['svn ignore']['filename'] = '.svnignore'
        self._dvcs['svn ignore']['function'] = self.ignore_file

        self._dvcs['cvs repository']['filename'] = 'CVS/Entries'
        self._dvcs['cvs repository']['function'] = self.cvs_entries

        self._dvcs['cvs ignore']['filename'] = '.cvsignore'
        self._dvcs['cvs ignore']['function'] = self.ignore_file

    def crawl(self, fuzzable_request):
        """
        For every directory, fetch a list of files and analyze the response.

        :param fuzzable_request: A fuzzable_request instance that contains
                                 (among other things) the URL to test.
        """
        domain_path = fuzzable_request.get_url().get_domain_path()

        if domain_path not in self._analyzed_dirs:
            self._analyzed_dirs.add(domain_path)

            test_generator = self._url_generator(domain_path)
            self.worker_pool.map_multi_args(self._send_and_check,
                                            test_generator)

    def _url_generator(self, domain_path):
        """
        Based on different URLs with directories, generate the URLs that need
        to be tested.

        :return: URLs
        """
        for repo in self._dvcs.keys():
            repo_url = domain_path.url_join(self._dvcs[repo]['filename'])
            function = self._dvcs[repo]['function']
            yield repo_url, function, repo, domain_path

    def _clean_filenames(self, filenames):
        """
        Filter some characters from filenames.

        :return: A clear list of filenames.
        """
        resources = set()

        for line in filenames:
            if line.startswith('/'):
                line = line[1:]
            if line.startswith('./'):
                line = line[2:]
            if line.endswith('/'):
                line = line[:-1]

            resources.add(line)

        return resources

    def _send_and_check(self, repo_url, repo_get_files, repo, domain_path):
        """
        Check if a repository index exists in the domain_path.

        :return: None, everything is saved to the self.out_queue.
        """
        http_response = self.http_get_and_parse(repo_url)

        if is_404(http_response):
            return

        filenames = repo_get_files(http_response.get_body())
        parsed_url_set = set()

        for filename in self._clean_filenames(filenames):
            test_url = domain_path.url_join(filename)
            if test_url not in self._analyzed_filenames:
                parsed_url_set.add(test_url)
                self._analyzed_filenames.add(filename)

        self.worker_pool.map(self.http_get_and_parse, parsed_url_set)

        if parsed_url_set:
            desc = ('A %s was found at: "%s"; this could indicate that'
                    ' a %s is accessible. You might be able to download'
                    ' the Web application source code.')
            desc %= repo, http_response.get_url(), repo

            v = Vuln('Source code repository', desc, severity.MEDIUM,
                     http_response.id, self.get_name())
            v.set_url(http_response.get_url())

            kb.kb.append(self, repo, v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def git_index(self, body):
        """
        Analyze the contents of the Git index and extract filenames.

        :param body: The contents of the file to analyze.
        :return: A list of filenames found.
        """
        filenames = set()
        signature = 'DIRC'
        offset = 12

        if body[:4] != signature:
            return set()

        version, = struct.unpack('>I', body[4:8])
        index_entries, = struct.unpack('>I', body[8:12])

        if version == 2:
            filename_offset = 62
        elif version == 3:
            filename_offset = 63
        else:
            return set()

        for _ in range(0, index_entries):
            offset += filename_offset - 1
            length, = struct.unpack('>B', body[offset:offset + 1])
            if length > (len(body) - offset):
                return set()
            filename = body[offset + 1:offset + 1 + length]
            padding = 8 - ((filename_offset + length) % 8)
            filenames.add(filename)
            offset += length + 1 + padding

        return filenames

    def hg_dirstate(self, body):
        """
        Analyze the contents of the HG dirstate and extract filenames.

        :param body: The contents of the file to analyze.
        :return: A list of filenames found.
        """
        filenames = set()
        offset = 53

        while offset < len(body):
            length, = struct.unpack('>I', body[offset:offset + 4])
            if length > (len(body) - offset):
                return set()
            offset += 4
            filename = body[offset:offset + length]
            offset += length + 13
            filenames.add(filename)

        return filenames

    def bzr_checkout_dirstate(self, body):
        """
        Analyze the contents of the BZR dirstate and extract filenames.

        :param body: The contents of the file to analyze.
        :return: A list of filenames found.
        """
        filenames = set()
        header = '#bazaar dirstate flat format '

        if body[0:29] != header:
            return set()

        body = body.split('\x00')
        found = True
        for offset in range(0, len(body)):
            filename = body[offset - 2]
            if body[offset] == 'd':
                if found:
                    filenames.add(filename)
                found = not found
            elif body[offset] == 'f':
                if found:
                    filenames.add(filename)
                found = not found

        return filenames

    def svn_entries(self, body):
        """
        Analyze the contents of the SVN entries and extract filenames.

        :param body: The contents of the file to analyze.
        :return: A list of filenames found.
        """
        filenames = set()
        lines = body.split('\n')
        offset = 29

        while offset < len(lines):
            line = lines[offset].strip()
            filename = lines[offset - 1].strip()
            if line == 'file':
                filenames.add(filename)
                offset += 34
            elif line == 'dir':
                filenames.add(filename)
                offset += 3

        return filenames

    def cvs_entries(self, body):
        """
        Analyze the contents of the CVS entries and extract filenames.

        :param body: The contents of the file to analyze.
        :return: A list of filenames found.
        """
        filenames = set()

        for line in body.split('\n'):
            if '/' in line:
                slashes = line.split('/')
                if len(slashes) != 6:
                    continue
                filenames.add(slashes[1])

        return filenames

    def filter_special_character(self, line):
        """
        Analyze the possible regexp contents and extract filenames or
        directories without regexp.

        :param line: A regexp filename or directory.
        :return: A real filename or directory.
        """
        special_characters = ['*', '?', '[', ']', ':']

        for char in special_characters:
            if char in line:
                l = line.split(char)[0]
                if '/' in l:
                    line = '/'.join(l.split('/')[:-1])
                else:
                    line = ''
                    break

        return line

    def ignore_file(self, body):
        """
        Analyze the contents of the Git, HG, BZR, SVN and CVS ignore file
        and extract filenames.

        :param body: The contents of the file to analyze.
        :return: A list of filenames found.
        """
        filenames = set()
        for line in body.split('\n'):

            line = line.strip()

            if line.startswith('#') or line == '':
                continue

            line = self.filter_special_character(line)
            if not line:
                continue

            if line.startswith('/') or line.startswith('^'):
                line = line[1:]
            if line.endswith('/') or line.endswith('$'):
                line = line[:-1]

            filenames.add(line)

        return filenames

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin search git, hg, bzr, svn or cvs repositories and checks for files containing.

        For example, if the input is:
            - http://host.tld/w3af/index.php

        The plugin will perform requests to:
            - http://host.tld/w3af/.git/index
            - http://host.tld/w3af/.gitignore
            - http://host.tld/w3af/.hg/store/fncache
            - http://host.tld/w3af/.hgignore
            - http://host.tld/w3af/.bzr/checkout/dirstate
            - http://host.tld/w3af/.bzrignore
            - http://host.tld/w3af/.svn/entries
            - http://host.tld/w3af/.svnignore
            - http://host.tld/w3af/CVS/Entries
            - http://host.tld/w3af/.cvsignore
            - http://host.tld/.git/index
            - http://host.tld/.gitignore
            - http://host.tld/.hg/store/fncache
            - http://host.tld/.hgignore
            - http://host.tld/.bzr/checkout/dirstate
            - http://host.tld/.bzrignore
            - http://host.tld/.svn/entries
            - http://host.tld/.svnignore
            - http://host.tld/CVS/Entries
            - http://host.tld/.cvsignore
        """
