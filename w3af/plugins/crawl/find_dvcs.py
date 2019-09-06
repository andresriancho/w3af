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
import os
import struct
import sqlite3
import tempfile

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.misc.temp_dir import get_temp_dir
from w3af.core.data.misc.encoding import smart_unicode
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.vuln import Vuln


class DVCSTest(object):
    def __init__(self, filename, name, method):
        self.filename = filename
        self.name = name
        self.method = method


class find_dvcs(CrawlPlugin):
    """
    Search Git, Mercurial (HG), Bazaar (BZR), Subversion (SVN) and CVS
    repositories and checks for files containing

    :author: Adam Baldwin (adam_baldwin@ngenuity-is.com)
    :author: Tomas Velazquez (tomas.velazquezz - gmail.com)
    :author: Andres Riancho (andres@andresriancho.com)
    """

    BAD_HTTP_CODES = {301, 302, 307}

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._analyzed_dirs = ScalableBloomFilter()
        self._analyzed_filenames = ScalableBloomFilter()

        self._dvcs = [DVCSTest('.git/index', 'git repository', self.git_index),
                      DVCSTest('.gitignore', 'git ignore', self.ignore_file),
                      DVCSTest('.hg/dirstate', 'hg repository', self.hg_dirstate),
                      DVCSTest('.hgignore', 'hg ignore', self.ignore_file),
                      DVCSTest('.bzr/checkout/dirstate', 'bzr repository', self.bzr_checkout_dirstate),
                      DVCSTest('.bzrignore', 'bzr ignore', self.ignore_file),
                      DVCSTest('.svn/entries', 'svn repository', self.svn_entries),
                      DVCSTest('.svn/wc.db', 'svn repository db', self.svn_wc_db),
                      DVCSTest('.svnignore', 'svn ignore', self.ignore_file),
                      DVCSTest('CVS/Entries', 'cvs repository', self.cvs_entries),
                      DVCSTest('.cvsignore', 'cvs ignore', self.ignore_file)]

    def crawl(self, fuzzable_request, debugging_id):
        """
        For every directory, fetch a list of files and analyze the response.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                 (among other things) the URL to test.
        """
        domain_path = fuzzable_request.get_url().get_domain_path()

        if domain_path in self._analyzed_dirs:
            return

        self._analyzed_dirs.add(domain_path)

        test_generator = self._url_generator(domain_path)
        self.worker_pool.map_multi_args(self._send_and_check, test_generator)

    def _url_generator(self, domain_path):
        """
        Based on different URLs with directories, generate the URLs that need
        to be tested.

        :return: URLs
        """
        for dvcs_test in self._dvcs:
            repo_url = domain_path.url_join(dvcs_test.filename)
            yield (repo_url,
                   dvcs_test.method,
                   dvcs_test.name,
                   domain_path)

    def _clean_filenames(self, filenames):
        """
        Filter some characters from filenames.

        :return: A clear list of filenames.
        """
        resources = set()

        for filename in filenames:

            # Sometimes we get random bytes from the .git/index because of
            # git versions we don't fully support, so we ignore any encoding
            # errors
            filename = smart_unicode(filename, errors='ignore')

            if filename.startswith('/'):
                filename = filename[1:]

            if filename.startswith('./'):
                filename = filename[2:]

            if filename.endswith('/'):
                filename = filename[:-1]

            resources.add(filename)

        return resources

    def _send_and_check(self, repo_url, repo_get_files, repo, domain_path):
        """
        Check if a repository index exists in the domain_path.

        :return: None, everything is saved to the self.out_queue.
        """
        # Here we use the new http_get instead of http_get_and_parse because
        # we want to check BAD_HTTP_CODES and the response body (see below)
        # before we send the response to the core
        http_response = self.http_get(repo_url,
                                      binary_response=True,
                                      respect_size_limit=False,
                                      grep=False)

        if is_404(http_response):
            return

        if http_response.get_code() in self.BAD_HTTP_CODES:
            return

        if not http_response.get_body():
            return

        try:
            filenames = repo_get_files(http_response.get_raw_body())
        except Exception, e:
            # We get here when the HTTP response is NOT a 404, but the response
            # body couldn't be properly parsed. This is usually because of a false
            # positive in the is_404 function, OR a new version-format of the file
            # to be parsed.
            #
            # Log in order to be able to improve the framework.
            args = (e, repo_get_files.__name__, repo_url)
            om.out.debug('Got a "%s" exception while running "%s" on "%s"' % args)
            return

        parsed_url_set = set()

        for filename in self._clean_filenames(filenames):
            test_url = domain_path.url_join(filename)
            if test_url in self._analyzed_filenames:
                continue

            parsed_url_set.add(test_url)
            self._analyzed_filenames.add(filename)

        if not parsed_url_set:
            return

        self.worker_pool.map(self.http_get_and_parse, parsed_url_set)

        # After performing the checks (404, redirects, body is not empty, body
        # can be parsed, body actually had filenames inside) send the URL to the
        # core
        fr = FuzzableRequest(repo_url, method='GET')
        self.output_queue.put(fr)

        # Now we send this finding to the report for manual analysis
        desc = ('A %s was found at: "%s"; this could indicate that a %s is'
                ' accessible. You might be able to download the Web'
                ' application source code.')
        desc %= (repo, http_response.get_url(), repo)

        v = Vuln('Source code repository', desc, severity.MEDIUM,
                 http_response.id, self.get_name())
        v.set_url(http_response.get_url())

        kb.kb.append(self, repo, v)
        om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def git_index(self, body):
        """
        Analyze the contents of the Git index and extract file names.

        :param body: The contents of the file to analyze.
        :return: A list of file names found.
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

        for _ in xrange(index_entries):
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
        for offset in xrange(len(body)):
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

        According to [0] the SVN entries file contains XML, but other sources [1]
        say that the file uses another format. Doing a "svn co" of various
        repositories and investigating the contents of the file makes me believe
        it is deprecated. The contents I see now are: "12".

        It seems to me that .svn/entries was deprecated and "12" is just a place-
        holder to indicate that the svn client should look somewhere else (most
        likely wc.db) for the data.

        I'm keeping this method because we might just be lucky and find
        an old repository, but a new SVN repository detection method using wc.db
        was also added.

        [0] http://svn.gnu.org.ua/svnbook/svn.developer.insidewc.html
        [1] http://svnbook.red-bean.com/en/1.6/svn.developer.insidewc.html

        :param body: The contents of the file to analyze.
        :return: A list of filenames found.
        """
        # See method documentation to understand why 12
        if body.strip() == '12':
            return set()

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

            else:
                # This prevents an endless loop when the document being parsed
                # is not a real SVN entries
                break

        return filenames

    def svn_wc_db(self, body):
        """
        Analyze the contents of the HTTP response body to identify if it is
        a SVN database (wc.db) and extract filenames.

        :param body: Potentially a wc.db file.
        :return: Filenames stored in the DB
        """
        filenames = set()

        temp_db = tempfile.NamedTemporaryFile(prefix='w3af-find-dvcs-',
                                              suffix='-wc.db',
                                              delete=False,
                                              dir=get_temp_dir())

        temp_db_fh = file(temp_db.name, 'w')
        temp_db_fh.write(body)
        temp_db_fh.close()

        query = ('SELECT local_relpath, '
                 ' ".svn/pristine/" || substr(checksum,7,2) || "/" || substr(checksum,7) || ".svn-base" AS svn'
                 ' FROM NODES WHERE kind="file"')

        try:
            conn = sqlite3.connect(temp_db.name)
            cursor = conn.cursor()

            cursor.execute(query)
            query_result = cursor.fetchall()

            for path, svn_path in query_result:
                filenames.add(path)
                filenames.add(svn_path)
        except Exception, e:
            msg = 'Failed to extract filenames from wc.db file. The exception was: "%s"'
            args = (e,)
            om.out.debug(msg % args)
        finally:
            if os.path.exists(temp_db.name):
                os.remove(temp_db.name)

        return filenames

    def cvs_entries(self, body):
        """
        Analyze the contents of the CVS entries and extract filenames.

        :param body: The contents of the file to analyze.
        :return: A list of filenames found.
        """
        filenames = set()

        for line in body.split('\n'):
            # https://docstore.mik.ua/orelly/other/cvs/cvs-CHP-6-SECT-9.htm
            #
            # /name/revision/timestamp[+conflict]/options/tagdate
            if not line.startswith('/'):
                continue

            # /name/revision/timestamp[+conflict]/options/tagdate
            tokens = line.split('/')
            if len(tokens) != 6:
                continue

            # Example value: Sun Apr 7 01:29:26 1996
            timestamp = tokens[2]
            if timestamp.count(':') <= 1:
                continue

            filenames.add(tokens[1])

        return filenames

    def filter_special_character(self, line):
        """
        Takes a line from .gitignore (or similar) and removes all the
        regular expression special characters.

        Example gitignore files:
            https://github.com/github/gitignore

        :param line: A line from gitignore
        :return: The same line, without the special characters.
        """
        special_characters = ['*', '?', '[', ']', ':', '!']

        for char in special_characters:
            line = line.replace(char, '')

        return line

    def ignore_file(self, body):
        """
        Analyze the contents of the Git, HG, BZR, SVN and CVS ignore file
        and extract file names.

        :param body: The contents of the file to analyze.
        :return: A list of file names found.
        """
        if body is None:
            return []

        filenames = set()
        for line in body.split('\n'):

            line = line.strip()

            # We sometimes get here because of a is_404 false positive, and the
            # function is trying to parse an HTML document as if it were a
            # DVCS ignore file.
            #
            # To prevent the is_404 false positive from propagating we detect
            # HTML tags, if those are found, return an empty list.
            if line.startswith('<') and line.endswith('>'):
                return []

            if line.startswith('#'):
                continue

            # Lines with spaces are usually good indicators of false positives
            if ' ' in line:
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
