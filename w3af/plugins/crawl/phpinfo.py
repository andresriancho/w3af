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
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.db.disk_set import DiskSet
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info import Info
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class phpinfo(CrawlPlugin):
    """
    Search PHP Info file and if it finds it will determine the version of PHP.
    :author: Viktor Gazdag ( woodspeed@gmail.com )
    :author: Aung Khant ( aungkhant[at]yehg.net )
    """
    PHP_VERSION_RE = re.compile('(<tr class="h"><td>\n|alt="PHP Logo" /></a>)'
                                '<h1 class="p">PHP Version (.*?)</h1>', re.I)
    SYSTEM_RE = re.compile('System </td><td class="v">(.*?)</td></tr>', re.I)

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._analyzed_dirs = DiskSet(table_prefix='phpinfo')
        self._has_audited = False

    def crawl(self, fuzzable_request):
        """
        For every directory, fetch a list of files and analyze the response.

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
        res = ['phpinfo.php', 'PhpInfo.php', 'PHPinfo.php', 'PHPINFO.php',
               'phpInfo.php', 'info.php', 'test.php?mode=phpinfo',
               'index.php?view=phpinfo', 'index.php?mode=phpinfo',
               'TEST.php?mode=phpinfo', '?mode=phpinfo', '?view=phpinfo',
               'install.php?mode=phpinfo', 'INSTALL.php?mode=phpinfo',
               'admin.php?mode=phpinfo', 'phpversion.php', 'phpVersion.php',
               'test1.php', 'phpinfo1.php', 'phpInfo1.php', 'info1.php',
               'PHPversion.php', 'x.php', 'xx.php', 'xxx.php']

        identified_os = kb.kb.raw_read('fingerprint_os', 'operating_system_str')

        if not isinstance(identified_os, basestring):
            identified_os = cf.cf.get('target_os')

        # pylint: disable=E1103
        if 'windows' in identified_os.lower():
            res = list(set([path.lower() for path in res]))
        # pylint: enable=E1103

        return res

    def _check_and_analyze(self, domain_path, php_info_filename):
        """
        Check if a php_info_filename exists in the domain_path.
        :return: None, everything is put() into the self.output_queue.
        """
        php_info_url = domain_path.url_join(php_info_filename)
        try:
            response = self._uri_opener.GET(php_info_url, cache=True)
        except BaseFrameworkException, w3:
            msg = 'Failed to GET phpinfo file: "%s". Exception: "%s".'
            om.out.debug(msg % (php_info_url, w3))
            return

        # Needs to exist
        if is_404(response):
            return

        # Create the fuzzable request and send it to the core
        fr = FuzzableRequest.from_http_response(response)
        self.output_queue.put(fr)

        # Check if it's a phpinfo file
        php_version = self.PHP_VERSION_RE.search(response.get_body(), re.I)
        sysinfo = self.SYSTEM_RE.search(response.get_body(), re.I)

        if php_version and sysinfo:
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
        analysis_methods = {self._register_globals, self._allow_url_fopen,
                            self._allow_url_include, self._display_errors,
                            self._expose_php, self._lowest_privilege_test,
                            self._disable_functions, self._curl_file_support,
                            self._cgi_force_redirect,
                            self._session_cookie_httponly,
                            self._session_use_trans, self._session_save_path,
                            self._default_charset, self._enable_dl,
                            self._memory_limit, self._post_max_size,
                            self._upload_max_filesize, self._upload_tmp_dir,
                            self._file_uploads, self._magic_quotes_gpc,
                            self._open_basedir, self._session_hash_function}

        for analysis_method in analysis_methods:
            analysis_method(response)

    def _register_globals(self, response):
        regex_str = 'register_globals</td><td class="v">(On|Off)</td>'
        register_globals = re.search(regex_str, response.get_body(), re.I)

        if register_globals:
            rg = register_globals.group(1)
            if rg == 'On':
                desc = 'The phpinfo()::register_globals is on.'
                v = Vuln('PHP register_globals: On', desc,
                         severity.MEDIUM, response.id, self.get_name())
                v.set_url(response.get_url())
                
                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())
            else:
                rg_name = 'PHP register_globals: Off'
                rg_desc = 'The phpinfo()::register_globals is off.'
                i = Info(rg_name, rg_desc, response.id, self.get_name())
                i.set_url(response.get_url())

                kb.kb.append(self, 'phpinfo', i)
                om.out.information(i.get_desc())

    def _allow_url_fopen(self, response):
        regex_str = 'allow_url_fopen</td><td class="v">(On|<i>no value</i>)</td>'
        allow_url_fopen = re.search(regex_str, response.get_body(), re.I)
        if allow_url_fopen:
            desc = 'The phpinfo()::allow_url_fopen is enabled.'
            v = Vuln('PHP allow_url_fopen: On', desc,
                     severity.MEDIUM, response.id, self.get_name())
            v.set_url(response.get_url())
            
            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _allow_url_include(self, response):
        regex_str = 'allow_url_include</td><td class="v">(On|<i>no value</i>)</td>'
        allow_url_include = re.search(regex_str, response.get_body(), re.I)
        if allow_url_include:
            desc = 'The phpinfo()::allow_url_include is enabled.'
            v = Vuln('PHP allow_url_include: On', desc,
                     severity.MEDIUM, response.id, self.get_name())
            v.set_url(response.get_url())
            
            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _display_errors(self, response):
        regex_str = 'display_errors</td><td class="v">(On|<i>no value</i>)</td>'
        display_errors = re.search(regex_str, response.get_body(), re.I)
        if display_errors:
            desc = 'The phpinfo()::display_errors is enabled.'
            v = Vuln('PHP display_errors: On', desc,
                     severity.MEDIUM, response.id, self.get_name())
            v.set_url(response.get_url())
            
            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _expose_php(self, response):
        regex_str = 'expose_php</td><td class="v">(On|<i>no value</i>)</td>'
        expose_php = re.search(regex_str, response.get_body(), re.I)
        if expose_php:
            desc = 'The phpinfo()::expose_php is enabled.'
            v = Vuln('PHP expose_php: On', desc,
                     severity.MEDIUM, response.id, self.get_name())
            v.set_url(response.get_url())
            
            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _lowest_privilege_test(self, response):
        regex_str = 'User/Group </td><td class="v">(.*?)\((\d.*?)\)/(\d.*?)</td>'
        lowest_privilege_test = re.search(regex_str, response.get_body(), re.I)
        if lowest_privilege_test:
            lpt_uname = lowest_privilege_test.group(1)
            lpt_uid = lowest_privilege_test.group(2)
            lpt_uid = int(lpt_uid)
            lpt_gid = lowest_privilege_test.group(3)
            if lpt_uid < 99 or lpt_gid < 99 or \
            re.match('root|apache|daemon|bin|operator|adm', lpt_uname, re.I):

                desc = 'phpinfo()::PHP may be executing as a higher privileged'\
                       ' group. Username: %s, UserID: %s, GroupID: %s.' 
                desc = desc % (lpt_uname, lpt_uid, lpt_gid)
                
                v = Vuln('PHP lowest_privilege_test:fail', desc,
                         severity.MEDIUM, response.id, self.get_name())
                v.set_url(response.get_url())

                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())
            else:
                lpt_name = 'privilege:' + lpt_uname
                lpt_desc = 'phpinfo()::PHP is executing under '
                lpt_desc += 'username: ' + lpt_uname + ', '
                lpt_desc += 'userID: ' + str(lpt_uid) + ', '
                lpt_desc += 'groupID: ' + lpt_gid
                i = Info(lpt_name, lpt_desc, response.id, self.get_name())
                i.set_url(response.get_url())

                kb.kb.append(self, 'phpinfo', i)
                om.out.information(i.get_desc())

    def _disable_functions(self, response):
        regex_str = 'disable_functions</td><td class="v">(.*?)</td>'
        disable_functions = re.search(regex_str, response.get_body(), re.I)
        if disable_functions:
            secure_df = 8
            df = disable_functions.group(1)
            dfe = df.split(',')
            if len(dfe) < secure_df:
                desc = 'The phpinfo()::disable_functions are set to few.'
                v = Vuln('PHP disable_functions:few', desc,
                         severity.MEDIUM, response.id, self.get_name())
                v.set_url(response.get_url())
                
                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _curl_file_support(self, response):
        regex_str = '<h1 class="p">PHP Version (\d).(\d).(\d)</h1>'
        curl_file_support = re.search(regex_str, response.get_body(), re.I)
        if curl_file_support:
            php_major_ver = curl_file_support.group(1)
            php_minor_ver = curl_file_support.group(2)
            php_rev_ver = curl_file_support.group(3)

            current_ver = php_major_ver + '.' + php_minor_ver + \
                '' + php_rev_ver
            current_ver = float(current_ver)
            php_major_ver = int(php_major_ver)
            php_minor_ver = int(php_minor_ver)
            php_rev_ver = int(php_rev_ver)

            cv4check = float(4.44)
            cv5check = float(5.16)
            curl_vuln = 1

            if php_major_ver == 4:
                if current_ver >= cv4check:
                    curl_vuln = 0
            elif php_major_ver == 5:
                if current_ver >= cv5check:
                    curl_vuln = 0
            elif php_major_ver >= 6:
                curl_vuln = 0
            else:
                curl_vuln = 0

            if curl_vuln == 1:
                desc = 'The phpinfo()::cURL::file_support has a security hole'\
                       ' present in this version of PHP allows the cURL'\
                       ' functions to bypass safe_mode and open_basedir'\
                       ' restrictions.'
                v = Vuln('PHP curl_file_support:not_fixed', desc,
                         severity.MEDIUM, response.id, self.get_name())
                v.set_url(response.get_url())
                
                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _cgi_force_redirect(self, response):
        regex_str = 'cgi_force_redirect</td><td class="v">(.*?)</td>'
        cgi_force_redirect = re.search(regex_str, response.get_body(), re.I)
        if cgi_force_redirect:
            utd = cgi_force_redirect.group(1) + ''
            if utd != 'On':
                desc = 'The phpinfo()::CGI::force_redirect is disabled.'
                v = Vuln('PHP cgi_force_redirect: Off', desc,
                         severity.MEDIUM, response.id, self.get_name())
                v.set_url(response.get_url())
                
                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _session_cookie_httponly(self, response):
        regex_str = 'session\.cookie_httponly</td><td class="v">(Off|no|0)</td>'
        session_cookie_httponly = re.search(regex_str, response.get_body(), re.I)
        if session_cookie_httponly:
            desc = 'The phpinfo()::session.cookie_httponly is off.'
            v = Vuln('PHP session.cookie_httponly: Off', desc,
                     severity.MEDIUM, response.id, self.get_name())
            v.set_url(response.get_url())
            
            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _session_save_path(self, response):
        regex_str = 'session\.save_path</td><td class="v">(<i>no value</i>)</td>'
        session_save_path = re.search(regex_str, response.get_body(), re.I)
        if session_save_path:
            desc = 'The phpinfo()::session.save_path may be set to world-'\
                   'accessible directory.'
            v = Vuln('PHP session_save_path:Everyone', desc,
                     severity.LOW, response.id, self.get_name())
            v.set_url(response.get_url())

            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _session_use_trans(self, response):
        regex_str = 'session\.use_trans</td><td class="v">(On)</td>'
        session_use_trans = re.search(regex_str, response.get_body(), re.I)
        if session_use_trans:
            desc = 'The phpinfo()::session.use_trans is enabled. This makes'\
                   ' session hijacking easier.'
            v = Vuln('PHP session_use_trans: On', desc,
                     severity.MEDIUM, response.id, self.get_name())
            v.set_url(response.get_url())
            
            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _default_charset(self, response):
        regex_str = 'default_charset</td><td class="v">(Off|no|0)</td>'
        default_charset = re.search(regex_str, response.get_body(), re.I)
        if default_charset:
            desc = 'The phpinfo()::default_charset is set to none. This'\
                   ' makes PHP scripts vulnerable to variable charset'\
                   ' encoding XSS.'
            v = Vuln('PHP default_charset: Off', desc,
                     severity.MEDIUM, response.id, self.get_name())
            v.set_url(response.get_url())
            
            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _enable_dl(self, response):
        regex_str = 'enable_dl</td><td class="v">(On|Off)</td>'
        enable_dl = re.search(regex_str, response.get_body(), re.I)
        if enable_dl:
            rg = enable_dl.group(1)
            if rg == 'On':
                desc = 'The phpinfo()::enable_dl is on.'
                v = Vuln('PHP enable_dl: On', desc,
                         severity.MEDIUM, response.id, self.get_name())
                v.set_url(response.get_url())
                
                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())
            else:
                ed_name = 'PHP enable_dl: Off'
                ed_desc = 'The phpinfo()::enable_dl is off.'
                i = Info(ed_name, ed_desc, response.id, self.get_name())
                i.set_url(response.get_url())

                kb.kb.append(self, 'phpinfo', i)
                om.out.information(i.get_desc())

    def _memory_limit(self, response):
        regex_str = 'memory_limit</td><td class="v">(\d.*?)</td>'
        memory_limit = re.search(regex_str, response.get_body(), re.I)
        if memory_limit:
            secure_ml = 10
            ml = memory_limit.group(1) + ''
            ml = ml.replace('M', '')
            if ml > secure_ml:
                desc = 'The phpinfo()::memory_limit is set to higher value'\
                       ' (%s).' % memory_limit.group(1)
                v = Vuln('PHP memory_limit:high', desc,
                         severity.MEDIUM, response.id, self.get_name())
                v.set_url(response.get_url())
                
                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _post_max_size(self, response):
        regex_str = 'post_max_size</td><td class="v">(\d.*?)</td>'
        post_max_size = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        if post_max_size:
            secure_pms = 20
            pms = post_max_size.group(1) + ''
            pms = pms.replace('M', '')
            pms = int(pms)
            if pms > secure_pms:
                desc = 'The phpinfo()::post_max_size is set to higher value'\
                       ' (%s).' % post_max_size.group(1)
                v = Vuln('PHP post_max_size:high', desc,
                         severity.LOW, response.id, self.get_name())
                v.set_url(response.get_url())

                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _upload_max_filesize(self, response):
        regex_str = 'upload_max_filesize</td><td class="v">(\d.*?)</td>'
        upload_max_filesize = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        if upload_max_filesize:
            secure_umf = 20
            umf = upload_max_filesize.group(1) + ''
            umf = umf.replace('M', '')
            umf = int(umf)
            if umf > secure_umf:
                desc = 'The phpinfo()::upload_max_filesize is set to higher'\
                       ' value (%s).' % upload_max_filesize.group(1)
                v = Vuln('PHP upload_max_filesize:high', desc,
                         severity.LOW, response.id, self.get_name())
                v.set_url(response.get_url())
                
                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _upload_tmp_dir(self, response):
        regex_str = 'upload_tmp_dir</td><td class="v">(<i>no value</i>)</td>'
        upload_tmp_dir = re.search(regex_str, response.get_body(), re.I)
        if upload_tmp_dir:
            desc = 'The phpinfo()::upload_tmp_dir may be set to world-'\
                   'accessible directory.'
            v = Vuln('PHP upload_tmp_dir:Everyone', desc,
                     severity.LOW, response.id, self.get_name())
            v.set_url(response.get_url())

            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _file_uploads(self, response):
        regex_str = 'file_uploads</td><td class="v">(On|<i>no value</i>)</td>'
        file_uploads = re.search(regex_str, response.get_body(), re.IGNORECASE)
        if file_uploads:
            desc = 'The phpinfo()::file_uploads is enabled.'
            i = Info('PHP file_uploads: On', desc, response.id, self.get_name())
            i.set_url(response.get_url())
            
            kb.kb.append(self, 'phpinfo', i)
            om.out.information(i.get_desc())

    def _magic_quotes_gpc(self, response):
        regex_str = 'magic_quotes_gpc</td><td class="v">(On|Off)</td>'
        magic_quotes_gpc = re.search(regex_str, response.get_body(), re.I)
        if magic_quotes_gpc:
            mqg = magic_quotes_gpc.group(1)
            
            if mqg == 'On':
                desc = 'The phpinfo()::magic_quotes_gpc is on.'
                i = Info('PHP magic_quotes_gpc: On', desc, response.id,
                         self.get_name())
                
            else:
                desc = 'The phpinfo()::magic_quotes_gpc is off.'
                i = Info('PHP magic_quotes_gpc: Off', desc, response.id,
                         self.get_name())
                
            i.set_url(response.get_url())
            kb.kb.append(self, 'phpinfo', i)
            om.out.information(i.get_desc())

    def _open_basedir(self, response):
        regex_str = 'open_basedir</td><td class="v">(.*?)</td>'
        open_basedir = re.search(regex_str, response.get_body(), re.I)

        if open_basedir:
            obd = open_basedir.group(1)

            if obd == '<i>no value</i>':
                desc = 'The phpinfo()::open_basedir is not set.'
                i = Info('PHP open_basedir:disabled', desc, response.id,
                         self.get_name())

            else:
                desc = 'The phpinfo()::open_basedir is set to %s.'
                desc %= open_basedir.group(1)
                i = Info('PHP open_basedir:enabled', desc, response.id,
                         self.get_name())
            
            i.set_url(response.get_url())
            kb.kb.append(self, 'phpinfo', i)
            om.out.information(i.get_desc())

    def _session_hash_function(self, response):
        regex_str = 'session\.hash_function</td><td class="v">(.*?)</td>'
        session_hash_function = re.search(regex_str, response.get_body(), re.I)
        if session_hash_function:
            
            if session_hash_function.group(1) == 0\
            or session_hash_function.group(1) != 'no':
                desc = 'The phpinfo()::session.hash_function use md5 algorithm.'
                i = Info('PHP session.hash_function:md5', desc, response.id,
                         self.get_name())
            else:
                desc = 'The phpinfo()::session.hash_function use sha algorithm.'
                i = Info('PHP session.hash_function:sha', desc, response.id,
                         self.get_name())

            i.set_url(response.get_url())
            
            kb.kb.append(self, 'phpinfo', i)
            om.out.information(i.get_desc())

    def end(self):
        self._analyzed_dirs.cleanup()

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
