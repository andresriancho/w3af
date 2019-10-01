"""
phpinfo.py

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

from itertools import repeat, izip

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.kb.config as cf
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.plugins.crawl.phpinfo_analysis.analysis import (register_globals,
                                                          allow_url_fopen,
                                                          allow_url_include,
                                                          display_errors,
                                                          expose_php,
                                                          lowest_privilege_test,
                                                          disable_functions,
                                                          curl_file_support,
                                                          cgi_force_redirect,
                                                          session_cookie_httponly,
                                                          session_save_path,
                                                          session_use_trans,
                                                          default_charset,
                                                          enable_dl,
                                                          memory_limit,
                                                          post_max_size,
                                                          upload_max_filesize,
                                                          upload_tmp_dir,
                                                          file_uploads,
                                                          magic_quotes_gpc,
                                                          open_basedir,
                                                          session_hash_function)


PHP_INFO_FILES = {
    'phpinfo.php',
    'PhpInfo.php',
    'PHPinfo.php',
    'PHPINFO.php',
    'phpInfo.php',
    'info.php',
    'test.php?mode=phpinfo',
    'index.php?view=phpinfo',
    'index.php?mode=phpinfo',
    'TEST.php?mode=phpinfo',
    'install.php?mode=phpinfo',
    'INSTALL.php?mode=phpinfo',
    'admin.php?mode=phpinfo',
    'phpversion.php',
    'phpVersion.php',
    'test1.php',
    'phpinfo1.php',
    'phpInfo1.php',
    'info1.php',
    'PHPversion.php',
    'x.php',
    'xx.php',
    'xxx.php'
}

PHP_INFO_FILES_LOWERCASE = {i.lower() for i in PHP_INFO_FILES}

ANALYSIS_FUNCTIONS = (register_globals,
                      allow_url_fopen,
                      allow_url_include,
                      display_errors,
                      expose_php,
                      lowest_privilege_test,
                      disable_functions,
                      curl_file_support,
                      cgi_force_redirect,
                      session_cookie_httponly,
                      session_save_path,
                      session_use_trans,
                      default_charset,
                      enable_dl,
                      memory_limit,
                      post_max_size,
                      upload_max_filesize,
                      upload_tmp_dir,
                      file_uploads,
                      magic_quotes_gpc,
                      open_basedir,
                      session_hash_function)


class phpinfo(CrawlPlugin):
    """
    Search PHP Info file and if it finds it will determine the version of PHP.

    :author: Viktor Gazdag (woodspeed@gmail.com)
    :author: Aung Khant (aungkhant[at]yehg.net)
    """

    PHP_VERSION_RE = re.compile('(<tr class="h"><td>\n|alt="PHP Logo" /></a>)'
                                '<h1 class="p">PHP Version (.*?)</h1>', re.I)
    SYSTEM_RE = re.compile('System </td><td class="v">(.*?)</td></tr>', re.I)

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._analyzed_dirs = ScalableBloomFilter()
        self._has_audited = False

    def crawl(self, fuzzable_request, debugging_id):
        """
        For every directory, fetch a list of files and analyze the response.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        for domain_path in fuzzable_request.get_url().get_directories():

            if domain_path in self._analyzed_dirs:
                continue
            
            self._analyzed_dirs.add(domain_path)

            url_repeater = repeat(domain_path)
            args = izip(url_repeater, self._get_potential_phpinfos())

            self.worker_pool.map_multi_args(self._check_and_analyze, args)

    def _get_potential_phpinfos(self):
        """
        :return: Filename of the php info file.
        """
        if self._should_use_lowercase_db():
            return PHP_INFO_FILES_LOWERCASE

        return PHP_INFO_FILES

    def _should_use_lowercase_db(self):
        # pylint: disable=E1103
        identified_os = kb.kb.raw_read('fingerprint_os', 'operating_system_str')

        if not isinstance(identified_os, basestring):
            identified_os = cf.cf.get('target_os')

        identified_os = identified_os.lower()
        # pylint: enable=E1103

        if 'windows' in identified_os:
            return True

        return False

    def _check_and_analyze(self, domain_path, php_info_filename):
        """
        Check if a php_info_filename exists in the domain_path.
        :return: None, everything is put() into the self.output_queue.
        """
        php_info_url = domain_path.url_join(php_info_filename)

        response = self._uri_opener.GET(php_info_url,
                                        cache=True,
                                        grep=False)

        if is_404(response):
            return

        # Check if it is a phpinfo file
        php_version = self.PHP_VERSION_RE.search(response.get_body(), re.I)
        sysinfo = self.SYSTEM_RE.search(response.get_body(), re.I)

        if not php_version:
            return

        if not sysinfo:
            return

        # Create the fuzzable request and send it to the core
        fr = FuzzableRequest.from_http_response(response)
        self.output_queue.put(fr)

        desc = ('The phpinfo() file was found at: %s. The version'
                ' of PHP is: "%s" and the system information is:'
                ' "%s".')
        desc %= (response.get_url(), php_version.group(2), sysinfo.group(1))

        v = Vuln('phpinfo() file found', desc, severity.MEDIUM,
                 response.id, self.get_name())
        v.set_url(response.get_url())

        kb.kb.append(self, 'phpinfo', v)
        om.out.vulnerability(v.get_desc(), severity=v.get_severity())

        if not self._has_audited:
            self._has_audited = True
            self.audit_phpinfo(response)

    def audit_phpinfo(self, response):
        """
        Scan for insecure php settings
        :return None
        """
        for analysis_method in ANALYSIS_FUNCTIONS:
            analysis_method(response)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin searches for the PHP Info file in all the directories and
        subdirectories that are sent as input and if it finds it will try to
        determine the version of the PHP. The PHP Info file holds information
        about the PHP and the system (version, environment, modules, extensions,
        compilation options, etc). For example, if the input is:
            - http://localhost/w3af/index.php

        The plugin will perform these requests:
            - http://localhost/w3af/phpinfo.php
            - http://localhost/phpinfo.php
            - ...
            - http://localhost/test.php?mode=phpinfo

        Once the phpinfo(); file is found the plugin also checks for probably
        insecure php settings and reports findings.
        """
