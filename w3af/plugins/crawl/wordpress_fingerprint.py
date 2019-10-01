"""
wordpress_fingerprint.py

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
import hashlib
import os
import re
import codecs

from collections import namedtuple
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af import ROOT_PATH
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import RunOnce, BaseFrameworkException
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.kb.info import Info
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class wordpress_fingerprint(CrawlPlugin):
    """
    Finds the version of a WordPress installation.
    :author: Ryan Dewhurst ( ryandewhurst@gmail.com ) www.ethicalhack3r.co.uk
    """
    # Wordpress version unique data, file/data/version
    WP_VERSIONS_XML = os.path.join(ROOT_PATH, 'plugins', 'crawl',
                                   'wordpress_fingerprint',
                                   'wp_versions.xml')
    
    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._exec = True
        self._release_db = os.path.join(ROOT_PATH, 'plugins', 'crawl',
                                        'wordpress_fingerprint', 'release.db')

    def crawl(self, fuzzable_request, debugging_id):
        """
        Finds the version of a WordPress installation.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                 (among other things) the URL to test.
        """
        if not self._exec:
            # This will remove the plugin from the crawl plugins to be run.
            raise RunOnce()

        #
        # Check if the server is running wp
        #
        domain_path = fuzzable_request.get_url().get_domain_path()

        # Main scan URL passed from w3af + unique wp file
        wp_unique_url = domain_path.url_join('wp-login.php')
        response = self._uri_opener.GET(wp_unique_url, cache=True)

        if is_404(response):
            return

        # It was possible to analyze wp-login.php, don't run again
        self._exec = False

        # Analyze the identified wordpress installation
        self._fingerprint_wordpress(domain_path, wp_unique_url,
                                    response)

    def _fingerprint_wordpress(self, domain_path, wp_unique_url, response):
        """
        Fingerprint wordpress using various techniques.
        """
        self._fingerprint_meta(domain_path, wp_unique_url, response)
        self._fingerprint_data(domain_path, wp_unique_url, response)
        self._fingerprint_readme(domain_path, wp_unique_url, response)
        self._fingerprint_installer(domain_path, wp_unique_url, response)

    def _fingerprint_installer(self, domain_path, wp_unique_url, response):
        """
        GET latest.zip and latest.tar.gz and compare with the hashes from the
        release.db that was previously generated from wordpress.org [0]
        and contains all release hashes.

        This gives the initial wordpress version, not the current one.

        [0] http://wordpress.org/download/release-archive/
        """
        zip_url = domain_path.url_join('latest.zip')
        tar_gz_url = domain_path.url_join('latest.tar.gz')
        install_urls = [zip_url, tar_gz_url]

        for install_url in install_urls:
            response = self._uri_opener.GET(install_url, cache=True,
                                            respect_size_limit=False)

            # md5sum the response body
            m = hashlib.md5()
            m.update(response.get_body())
            remote_release_hash = m.hexdigest()

            release_db = self._release_db

            for line in file(release_db):
                try:
                    line = line.strip()
                    release_db_hash, release_db_name = line.split(',')
                except:
                    continue

                if release_db_hash == remote_release_hash:

                    desc = ('The sysadmin used WordPress version "%s" during the'
                            ' installation, which was found by matching the contents'
                            ' of "%s" with the hashes of known releases. If the'
                            ' sysadmin did not update wordpress, the current version'
                            ' will still be the same.')
                    desc %= (release_db_name, install_url)

                    i = Info('Fingerprinted Wordpress version', desc, response.id,
                             self.get_name())
                    i.set_url(install_url)
                    
                    kb.kb.append(self, 'info', i)
                    om.out.information(i.get_desc())

                    # Send link to core
                    fr = FuzzableRequest(response.get_uri())
                    self.output_queue.put(fr)

    def _fingerprint_readme(self, domain_path, wp_unique_url, response):
        """
        GET the readme.html file and extract the version information from there.
        """
        wp_readme_url = domain_path.url_join('readme.html')
        response = self._uri_opener.GET(wp_readme_url, cache=True)

        # Find the string in the response html
        find = '<br /> Version (\d\.\d\.?\d?)'
        m = re.search(find, response.get_body())

        # If string found, group version
        if m:
            version = m.group(1)

            desc = 'WordPress version "%s" found in the readme.html file.'
            desc %= version

            i = Info('Fingerprinted WordPress version', desc, response.id,
                     self.get_name())
            i.set_url(wp_readme_url)
            
            kb.kb.append(self, 'info', i)
            om.out.information(i.get_desc())

            # Send link to core
            fr = FuzzableRequest(response.get_uri())
            self.output_queue.put(fr)

    def _fingerprint_meta(self, domain_path, wp_unique_url, response):
        """
        Check if the wp version is in index header
        """
        # Main scan URL passed from w3af + wp index page
        wp_index_url = domain_path.url_join('index.php')
        response = self._uri_opener.GET(wp_index_url, cache=True)

        # Find the string in the response html
        find = '<meta name="generator" content="[Ww]ord[Pp]ress (\d\.\d\.?\d?)" />'
        m = re.search(find, response.get_body())

        # If string found, group version
        if m:
            version = m.group(1)

            # Save it to the kb!
            desc = 'WordPress version "%s" found in the index header.'
            desc = desc % version

            i = Info('Fingerprinted WordPress version', desc, response.id,
                     self.get_name())
            i.set_url(wp_index_url)
            
            kb.kb.append(self, 'info', i)
            om.out.information(i.get_desc())

            # Send link to core
            fr = FuzzableRequest(response.get_uri())
            self.output_queue.put(fr)

    def _fingerprint_data(self, domain_path, wp_unique_url, response):
        """
        Find wordpress version from data
        """
        for wp_fingerprint in self._get_wp_fingerprints():
            
            # The URL in the XML is relative AND it has two different variables
            # that we need to replace:
            #        $wp-content$    -> wp-content/
            #        $wp-plugins$    -> wp-content/plugins/
            path = wp_fingerprint.filepath
            path = path.replace('$wp-content$', 'wp-content/')
            path = path.replace('$wp-plugins$', 'wp-content/plugins/')
            test_url = domain_path.url_join(path)
            
            response = self._uri_opener.GET(test_url, cache=True)

            response_hash = hashlib.md5(response.get_body()).hexdigest()

            if response_hash == wp_fingerprint.hash:
                version = wp_fingerprint.version

                # Save it to the kb!
                desc = ('WordPress version "%s" fingerprinted by matching known md5'
                        ' hashes to HTTP responses of static resources available at'
                        ' the remote WordPress install.')
                desc %= version
                i = Info('Fingerprinted WordPress version', desc, response.id,
                         self.get_name())
                i.set_url(test_url)
        
                kb.kb.append(self, 'info', i)
                om.out.information(i.get_desc())

                # Send link to core
                fr = FuzzableRequest(response.get_uri())
                self.output_queue.put(fr)

                break

    def _get_wp_fingerprints(self):
        """
        :return: Parse the XML and return a list of fingerprints.
        """
        try:
            wordpress_fp_fd = codecs.open(self.WP_VERSIONS_XML, 'r', 'utf-8',
                                          errors='ignore')
        except Exception, e:
            msg = 'Failed to open wordpress fingerprint database "%s": "%s".'
            args = (self.WP_VERSIONS_XML, e)
            raise BaseFrameworkException(msg % args)
        
        parser = make_parser()
        wp_handler = WPVersionsHandler()
        parser.setContentHandler(wp_handler)
        om.out.debug('Starting the wordpress fingerprint xml parsing. ')
        
        try:
            parser.parse(wordpress_fp_fd)
        except Exception, e:
            msg = 'XML parsing error in wordpress version DB, exception: "%s".'
            raise BaseFrameworkException(msg % e)
        
        om.out.debug('Finished xml parsing. ')
        
        return wp_handler.fingerprints
    
    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds the version of a WordPress installation by fingerprinting
        it.

        It first checks whether or not the version is in the index header and
        then it checks for the "real version" through the existance of files
        that are only present in specific versions.
        """


class WPVersionsHandler(ContentHandler):
    """
    Parse https://github.com/wpscanteam/wpscan/blob/master/data/wp_versions.xml
    
    Example content:
    
    <file src="wp-layout.css">
      <hash md5="7140e06c00ed03d2bb3dad7672557510">
        <version>1.2.1</version>
      </hash>
    
      <hash md5="1bcc9253506c067eb130c9fc4f211a2f">
        <version>1.2-delta</version>
      </hash>
    </file>
    """
    def __init__(self):
        self.file_src = ''
        self.hash_md5 = ''
        self.version = ''
        
        self.inside_version = False
        
        self.fingerprints = []

    def startElement(self, name, attrs):
        if name == 'file':
            self.file_src = attrs.get('src')
        elif name == 'hash':
            self.hash_md5 = attrs.get('md5')
        elif name == 'version':
            self.inside_version = True
            self.version = ''
        return

    def characters(self, ch):
        if self.inside_version:
            self.version += ch

    def endElement(self, name):
        if name == 'version':
            self.inside_version = False
        if name == 'hash':
            fp = FileFingerPrint(self.file_src, self.hash_md5, self.version)
            self.fingerprints.append(fp)


FileFingerPrint = namedtuple('FileFingerPrint', ['filepath', 'hash', 'version'])
