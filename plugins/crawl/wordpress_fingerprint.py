'''
wordpress_fingerprint.py

Copyright 2006 Andres Riancho

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

'''
import hashlib
import os
import re

import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb
import core.data.kb.info as info

from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.exceptions import w3afRunOnce
from core.controllers.core_helpers.fingerprint_404 import is_404


class wordpress_fingerprint(CrawlPlugin):
    '''
    Finds the version of a WordPress installation.
    @author: Ryan Dewhurst ( ryandewhurst@gmail.com ) www.ethicalhack3r.co.uk
    '''
    # Wordpress version unique data, file/data/version
    WP_FINGERPRINT = [(
        'wp-includes/js/tinymce/tiny_mce.js', '2009-05-25', '2.8'),
        ('wp-includes/js/thickbox/thickbox.css',
         '-ms-filter:', '2.7.1'),
        ('wp-admin/css/farbtastic.css', '.farbtastic', '2.7'),
        ('wp-includes/js/tinymce/wordpress.css',
         '-khtml-border-radius:', '2.6.1, 2.6.2, 2.6.3 or 2.6.5'),
        ('wp-includes/js/tinymce/tiny_mce.js', '0.7', '2.5.1'),
        ('wp-admin/async-upload.php', '200', '2.5'),
        ('wp-includes/images/rss.png',
         '200', '2.3.1, 2.3.2 or 2.3.3'),
        ('readme.html', '2.3', '2.3'),
        ('wp-includes/rtl.css', '#adminmenu a', '2.2.3'),
        ('wp-includes/js/wp-ajax.js', 'var a = $H();', '2.2.1'),
        ('wp-app.php', '200', '2.2')
    ]

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._exec = True
        self._release_db = os.path.join('plugins', 'crawl',
                                        'wordpress_fingerprint', 'release.db')

    def crawl(self, fuzzable_request):
        '''
        Finds the version of a WordPress installation.
        @param fuzzable_request: A fuzzable_request instance that contains
        (among other things) the URL to test.
        '''
        if not self._exec:
            # This will remove the plugin from the crawl plugins to be run.
            raise w3afRunOnce()

        else:
            #
            # Check if the server is running wp
            #
            domain_path = fuzzable_request.get_url().get_domain_path()

            # Main scan URL passed from w3af + unique wp file
            wp_unique_url = domain_path.url_join('wp-login.php')
            response = self._uri_opener.GET(wp_unique_url, cache=True)

            # If wp_unique_url is not 404, wordpress = true
            if not is_404(response):
                # It was possible to analyze wp-login.php, don't run again
                self._exec = False

                # Analyze the identified wordpress installation
                self._fingerprint_wordpress(
                    domain_path, wp_unique_url, response)

                # Extract the links
                for fr in self._create_fuzzable_requests(response):
                    self.output_queue.put(fr)

    def _fingerprint_wordpress(self, domain_path, wp_unique_url, response):
        '''
        Fingerprint wordpress using various techniques.
        '''
        self._fingerprint_meta(domain_path, wp_unique_url, response)
        self._fingerprint_data(domain_path, wp_unique_url, response)
        self._fingerprint_readme(domain_path, wp_unique_url, response)
        self._fingerprint_installer(domain_path, wp_unique_url, response)

    def _fingerprint_installer(self, domain_path, wp_unique_url, response):
        '''
        GET latest.zip and latest.tar.gz and compare with the hashes from the
        release.db that was previously generated from wordpress.org [0]
        and contains all release hashes.

        This gives the initial wordpress version, not the current one.

        [0] http://wordpress.org/download/release-archive/
        '''
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

                    # Save it to the kb!
                    i = info.info()
                    i.set_plugin_name(self.get_name())
                    i.set_name('WordPress version')
                    i.set_url(install_url)
                    i.set_id(response.id)
                    msg = 'The sysadmin used WordPress version "%s" during the'
                    msg += ' installation, which was found by matching the contents'
                    msg += ' of "%s" with the hashes of known releases. If the'
                    msg += ' sysadmin did not update wordpress, the current version'
                    msg += ' will still be the same.'
                    i.set_desc(msg % (release_db_name, install_url))
                    kb.kb.append(self, 'info', i)
                    om.out.information(i.get_desc())

    def _fingerprint_readme(self, domain_path, wp_unique_url, response):
        '''
        GET the readme.html file and extract the version information from there.
        '''
        wp_readme_url = domain_path.url_join('readme.html')
        response = self._uri_opener.GET(wp_readme_url, cache=True)

        # Find the string in the response html
        find = '<br /> Version (\d\.\d\.?\d?)'
        m = re.search(find, response.get_body())

        # If string found, group version
        if m:
            version = m.group(1)

            # Save it to the kb!
            i = info.info()
            i.set_plugin_name(self.get_name())
            i.set_name('WordPress version')
            i.set_url(wp_readme_url)
            i.set_id(response.id)
            msg = 'WordPress version "%s" found in the readme.html file.'
            i.set_desc(msg % version)
            kb.kb.append(self, 'info', i)
            om.out.information(i.get_desc())

    def _fingerprint_meta(self, domain_path, wp_unique_url, response):
        '''
        Check if the wp version is in index header
        '''
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
            i = info.info()
            i.set_plugin_name(self.get_name())
            i.set_name('WordPress version')
            i.set_url(wp_index_url)
            i.set_id(response.id)
            msg = 'WordPress version "%s" found in the index header.'
            i.set_desc(msg % version)
            kb.kb.append(self, 'info', i)
            om.out.information(i.get_desc())

    def _fingerprint_data(self, domain_path, wp_unique_url, response):
        '''
        Find wordpress version from data
        '''
        version = 'lower than 2.2'

        for url, match_string, wp_version in self.WP_FINGERPRINT:
            test_url = domain_path.url_join(url)
            response = self._uri_opener.GET(test_url, cache=True)

            if match_string == '200' and not is_404(response):
                version = wp_version
                break
            elif match_string in response.get_body():
                version = wp_version
                break

        # Save it to the kb!
        i = info.info()
        i.set_plugin_name(self.get_name())
        i.set_name('WordPress version')
        i.set_url(test_url)
        i.set_id(response.id)
        i.set_desc('WordPress version "' + version + '" found from data.')
        kb.kb.append(self, 'info', i)
        om.out.information(i.get_desc())

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds the version of a WordPress installation by fingerprinting
        it.

        It first checks whether or not the version is in the index header and
        then it checks for the "real version" through the existance of files
        that are only present in specific versions.
        '''
