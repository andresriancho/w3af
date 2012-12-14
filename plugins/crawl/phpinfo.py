'''
phpinfo.py

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
import re

from itertools import repeat, izip

import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb
import core.data.kb.config as cf
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity
import core.data.kb.info as info

from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.exceptions import w3afException
from core.controllers.core_helpers.fingerprint_404 import is_404
from core.data.db.disk_set import disk_set


class phpinfo(CrawlPlugin):
    '''
    Search PHP Info file and if it finds it will determine the version of PHP.
    @author: Viktor Gazdag ( woodspeed@gmail.com )
    '''

    '''
    CHANGELOG:
        Feb/17/2009- Added PHP Settings Audit Checks by Aung Khant (aungkhant[at]yehg.net)
    '''

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._analyzed_dirs = disk_set()
        self._has_audited = 0

    def crawl(self, fuzzable_request):
        '''
        For every directory, fetch a list of files and analyze the response.

        @param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''
        for domain_path in fuzzable_request.get_url().get_directories():

            if domain_path not in self._analyzed_dirs:
                self._analyzed_dirs.add(domain_path)

                url_repeater = repeat(domain_path)
                args = izip(url_repeater, self._get_potential_phpinfos())

                self.worker_pool.map_multi_args(
                    self._check_and_analyze, args)

    def _check_and_analyze(self, domain_path, php_info_filename):
        '''
        Check if a php_info_filename exists in the domain_path.
        @return: None, everything is put() into the self.output_queue.
        '''
        # Request the file
        php_info_url = domain_path.url_join(php_info_filename)
        try:
            response = self._uri_opener.GET(php_info_url, cache=True)
            om.out.debug('[phpinfo] Testing "' + php_info_url + '".')
        except w3afException, w3:
            msg = 'Failed to GET phpinfo file: "' + php_info_url + '".'
            msg += 'Exception: "' + str(w3) + '".'
            om.out.debug(msg)
        else:
            # Feb/17/2009 by Aung Khant:
            # when scanning phpinfo in window box
            # the problem is generating a lot of results
            # due to all-the-same-for-windows files phpVersion.php, phpversion.php ..etc
            # Well, how to solve it?
            # Finding one phpinfo file is enough for auditing for the target
            # So, we report every phpinfo file found
            # but we do and report auditing once. Sounds logical?
            #
            # Feb/17/2009 by Andres Riancho:
            # Yes, that sounds ok for me.

            # Check if it's a phpinfo file
            if not is_404(response):

                # Create the fuzzable request
                for fr in self._create_fuzzable_requests(response):
                    self.output_queue.put(fr)

                '''
                |Modified|
                old: regex_str = 'alt="PHP Logo" /></a><h1 class="p">PHP Version (.*?)</h1>'
                new: regex_str = '(<tr class="h"><td>\n|alt="PHP Logo" /></a>)<h1 class="p">PHP Version (.*?)</h1>'

                by aungkhant - I've been seeing phpinfo pages which don't print php logo image.
                One example, ning.com.

                '''
                regex_str = '(<tr class="h"><td>\n|alt="PHP Logo" /></a>)<h1 class="p">PHP Version (.*?)</h1>'
                php_version = re.search(
                    regex_str, response.get_body(), re.IGNORECASE)

                regex_str = 'System </td><td class="v">(.*?)</td></tr>'
                sysinfo = re.search(
                    regex_str, response.get_body(), re.IGNORECASE)

                if (php_version and sysinfo):
                    v = vuln.vuln()
                    v.set_plugin_name(self.get_name())
                    v.set_id(response.id)
                    v.set_name('phpinfo() file found')
                    v.set_severity(severity.MEDIUM)
                    v.set_url(response.get_url())
                    desc = 'The phpinfo() file was found at: ' + v.get_url()
                    desc += '. The version of PHP is: "' + php_version.group(2)
                    desc += '" and the system information is: "' + \
                        sysinfo.group(1)
                    desc += '".'
                    v.set_desc(desc)
                    kb.kb.append(self, 'phpinfo', v)
                    om.out.vulnerability(
                        v.get_desc(), severity=v.get_severity())
                    if (self._has_audited == 0):
                        self.audit_phpinfo(response)
                        self._has_audited = 1

    def audit_phpinfo(self, response):
        '''
        Scan for insecure php settings
        @author: Aung Khant (aungkhant[at]yehg.net)
        @return none

        two divisions: vulnerable settings and useful informative settings

        '''

        ##### [Vulnerable Settings] #####

        ### [register_globals] ###
        regex_str = 'register_globals</td><td class="v">(On|Off)</td>'
        register_globals = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        rg_flag = ''
        if register_globals:
            rg = register_globals.group(1)
            if(rg == 'On'):
                v = vuln.vuln()
                v.set_plugin_name(self.get_name())
                v.set_id(response.id)
                v.set_name('register_globals: On')
                v.set_severity(severity.MEDIUM)
                v.set_url(response.get_url())
                desc = 'The phpinfo()::register_globals is on.'
                v.set_desc(desc)
                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())
            else:
                rg_flag = 'info'
                rg_name = 'register_globals: Off'
                rg_desc = 'The phpinfo()::register_globals is off.'

        ### [/register_globals] ###

        ### [allow_url_fopen] ###
        regex_str = 'allow_url_fopen</td><td class="v">(On|<i>no value</i>)</td>'
        allow_url_fopen = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        if allow_url_fopen:
            v = vuln.vuln()
            v.set_plugin_name(self.get_name())
            v.set_id(response.id)
            v.set_name('allow_url_fopen: On')
            v.set_severity(severity.MEDIUM)
            v.set_url(response.get_url())
            desc = 'The phpinfo()::allow_url_fopen is enabled.'
            v.set_desc(desc)
            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())
        ### [/allow_url_fopen] ###

        ### [allow_url_include] ###
        regex_str = 'allow_url_include</td><td class="v">(On|<i>no value</i>)</td>'
        allow_url_include = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        if allow_url_include:
            v = vuln.vuln()
            v.set_plugin_name(self.get_name())
            v.set_id(response.id)
            v.set_name('allow_url_include: On')
            v.set_severity(severity.MEDIUM)
            v.set_url(response.get_url())
            desc = 'The phpinfo()::allow_url_include is enabled.'
            v.set_desc(desc)
            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())
        ### [/allow_url_include] ###

        ### [display_errors] ###
        regex_str = 'display_errors</td><td class="v">(On|<i>no value</i>)</td>'
        display_errors = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        if display_errors:
            v = vuln.vuln()
            v.set_plugin_name(self.get_name())
            v.set_id(response.id)
            v.set_name('display_errors: On')
            v.set_severity(severity.MEDIUM)
            v.set_url(response.get_url())
            desc = 'The phpinfo()::display_errors is enabled.'
            v.set_desc(desc)
            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())
        ### [/display_errors] ###

        ### [expose_php] ###
        regex_str = 'expose_php</td><td class="v">(On|<i>no value</i>)</td>'
        expose_php = re.search(regex_str, response.get_body(), re.IGNORECASE)
        if expose_php:
            v = vuln.vuln()
            v.set_plugin_name(self.get_name())
            v.set_id(response.id)
            v.set_name('expose_php: On')
            v.set_severity(severity.MEDIUM)
            v.set_url(response.get_url())
            desc = 'The phpinfo()::expose_php is enabled.'
            v.set_desc(desc)
            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())
        ### [/expose_php] ###

        ### [lowest_privilege_test] ###
        regex_str = 'User/Group </td><td class="v">(.*?)\((\d.*?)\)/(\d.*?)</td>'
        lowest_privilege_test = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        lpt_flag = ''
        if lowest_privilege_test:
            lpt_uname = lowest_privilege_test.group(1)
            lpt_uid = lowest_privilege_test.group(2)
            lpt_uid = int(lpt_uid)
            lpt_gid = lowest_privilege_test.group(3)
            if(lpt_uid < 99 or lpt_gid < 99 or re.match('root|apache|daemon|bin|operator|adm', lpt_uname, re.IGNORECASE)):
                v = vuln.vuln()
                v.set_plugin_name(self.get_name())
                v.set_id(response.id)
                v.set_name('lowest_privilege_test:fail')
                v.set_severity(severity.MEDIUM)
                v.set_url(response.get_url())
                desc = 'phpinfo()::PHP may be executing as a higher privileged group. '
                desc += 'Username: ' + lpt_uname + ', '
                desc += 'UserID: ' + str(lpt_uid) + ', '
                desc += 'GroupID: ' + lpt_gid
                v.set_desc(desc)
                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())
            else:
                lpt_flag = 'info'
                lpt_name = 'privilege:' + lpt_uname
                lpt_desc = 'phpinfo()::PHP is executing under '
                lpt_desc += 'username: ' + lpt_uname + ', '
                lpt_desc += 'userID: ' + str(lpt_uid) + ', '
                lpt_desc += 'groupID: ' + lpt_gid
        ### [/lowest_privilege_test] ###

        ### [disable_functions] ###
        regex_str = 'disable_functions</td><td class="v">(.*?)</td>'
        disable_functions = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        if disable_functions:
            secure_df = 8
            df = disable_functions.group(1)
            dfe = df.split(',')
            if(len(dfe) < secure_df):
                v = vuln.vuln()
                v.set_plugin_name(self.get_name())
                v.set_id(response.id)
                v.set_name('disable_functions:few')
                v.set_severity(severity.MEDIUM)
                v.set_url(response.get_url())
                desc = 'The phpinfo()::disable_functions are set to few.'
                v.set_desc(desc)
                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())
        ### [/disable_functions] ###

        ### [curl_file_support] ###
        regex_str = '<h1 class="p">PHP Version (\d).(\d).(\d)</h1>'
        curl_file_support = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
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

            if(php_major_ver == 4):
                if (current_ver >= cv4check):
                    curl_vuln = 0
            elif (php_major_ver == 5):
                if (current_ver >= cv5check):
                    curl_vuln = 0
            elif (php_major_ver >= 6):
                curl_vuln = 0
            else:
                curl_vuln = 0

            if(curl_vuln == 1):
                v = vuln.vuln()
                v.set_plugin_name(self.get_name())
                v.set_id(response.id)
                v.set_name('curl_file_support:not_fixed')
                v.set_severity(severity.MEDIUM)
                v.set_url(response.get_url())
                desc = 'The phpinfo()::cURL::file_support has a security hole present in this'
                desc += ' version of PHP allows the cURL functions to bypass safe_mode and'
                desc += ' open_basedir restrictions.  .'
                v.set_desc(desc)
                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())
        ### [/curl_file_support] ###

        ### [cgi_force_redirect] ###
        regex_str = 'cgi_force_redirect</td><td class="v">(.*?)</td>'
        cgi_force_redirect = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        if cgi_force_redirect:
            utd = cgi_force_redirect.group(1) + ''
            if(utd != 'On'):
                v = vuln.vuln()
                v.set_plugin_name(self.get_name())
                v.set_id(response.id)
                v.set_name('cgi_force_redirect: Off')
                v.set_severity(severity.MEDIUM)
                v.set_url(response.get_url())
                desc = 'The phpinfo()::CGI::force_redirect is disabled.'
                v.set_desc(desc)
                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())
        ### [/cgi_force_redirect] ###

        ### [session_cookie_httponly] ###
        regex_str = 'session\.cookie_httponly</td><td class="v">(Off|no|0)</td>'
        session_cookie_httponly = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        if session_cookie_httponly:
            v = vuln.vuln()
            v.set_plugin_name(self.get_name())
            v.set_id(response.id)
            v.set_name('session.cookie_httponly: Off')
            v.set_severity(severity.MEDIUM)
            v.set_url(response.get_url())
            desc = 'The phpinfo()::session.cookie_httponly is off.'
            v.set_desc(desc)
            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())
        ### [/session_cookie_httponly] ###

        ### [session_save_path] ###
        regex_str = 'session\.save_path</td><td class="v">(<i>no value</i>)</td>'
        session_save_path = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        if session_save_path:
            v = vuln.vuln()
            v.set_plugin_name(self.get_name())
            v.set_id(response.id)
            v.set_name('session_save_path:Everyone')
            v.set_severity(severity.LOW)
            v.set_url(response.get_url())
            desc = 'The phpinfo()::session.save_path may be set to world-accessible directory.'
            v.set_desc(desc)
            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())
        ### [/session_save_path] ###

        ### [session_use_trans] ###
        regex_str = 'session\.use_trans</td><td class="v">(On)</td>'
        session_use_trans = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        if session_use_trans:
            v = vuln.vuln()
            v.set_plugin_name(self.get_name())
            v.set_id(response.id)
            v.set_name('session_use_trans: On')
            v.set_severity(severity.MEDIUM)
            v.set_url(response.get_url())
            desc = 'The phpinfo()::session.use_trans is enabled. This makes session hijacking easier.'
            v.set_desc(desc)
            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())
        ### [/session_use_trans] ###

        ### [default_charset] ###
        regex_str = 'default_charset</td><td class="v">(Off|no|0)</td>'
        default_charset = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        if default_charset:
            v = vuln.vuln()
            v.set_plugin_name(self.get_name())
            v.set_id(response.id)
            v.set_name('default_charset: Off')
            v.set_severity(severity.MEDIUM)
            v.set_url(response.get_url())
            desc = 'The phpinfo()::default_charset is set to none. This makes PHP scripts vulnerable'
            desc += ' to variable charset encoding XSS.'
            v.set_desc(desc)
            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())
        ### [/default_charset] ###

        ### [enable_dl] ###
        regex_str = 'enable_dl</td><td class="v">(On|Off)</td>'
        enable_dl = re.search(regex_str, response.get_body(), re.IGNORECASE)
        ed_flag = ''
        if enable_dl:
            rg = enable_dl.group(1)
            if(rg == 'On'):
                v = vuln.vuln()
                v.set_plugin_name(self.get_name())
                v.set_id(response.id)
                v.set_name('enable_dl: On')
                v.set_severity(severity.MEDIUM)
                v.set_url(response.get_url())
                desc = 'The phpinfo()::enable_dl is on.'
                v.set_desc(desc)
                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())
            else:
                ed_flag = 'info'
                ed_name = 'enable_dl: Off'
                ed_desc = 'The phpinfo()::enable_dl is off.'
        ### [/enable_dl] ###

        ### [memory_limit] ###
        regex_str = 'memory_limit</td><td class="v">(\d.*?)</td>'
        memory_limit = re.search(regex_str, response.get_body(), re.IGNORECASE)
        if memory_limit:
            secure_ml = 10
            ml = memory_limit.group(1) + ''
            ml = ml.replace('M', '')
            if(ml > secure_ml):
                v = vuln.vuln()
                v.set_plugin_name(self.get_name())
                v.set_id(response.id)
                v.set_name('memory_limit:high')
                v.set_severity(severity.MEDIUM)
                v.set_url(response.get_url())
                desc = 'The phpinfo()::memory_limit is set to higher value (' + \
                    memory_limit.group(1) + ').'
                v.set_desc(desc)
                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())
        ### [/memory_limit] ###

        ### [post_max_size] ###
        regex_str = 'post_max_size</td><td class="v">(\d.*?)</td>'
        post_max_size = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        if post_max_size:
            secure_pms = 20
            pms = post_max_size.group(1) + ''
            pms = pms.replace('M', '')
            pms = int(pms)
            if(pms > secure_pms):
                v = vuln.vuln()
                v.set_plugin_name(self.get_name())
                v.set_id(response.id)
                v.set_name('post_max_size:high')
                v.set_severity(severity.LOW)
                v.set_url(response.get_url())
                desc = 'The phpinfo()::post_max_size is set to higher value (' + post_max_size.group(1) + ').'
                v.set_desc(desc)
                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())
        ### [/post_max_size] ###

        ### [upload_max_filesize] ###
        regex_str = 'upload_max_filesize</td><td class="v">(\d.*?)</td>'
        upload_max_filesize = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        if upload_max_filesize:
            secure_umf = 20
            umf = upload_max_filesize.group(1) + ''
            umf = umf.replace('M', '')
            umf = int(umf)
            if(umf > secure_umf):
                v = vuln.vuln()
                v.set_plugin_name(self.get_name())
                v.set_id(response.id)
                v.set_name('post_max_size:high')
                v.set_severity(severity.LOW)
                v.set_url(response.get_url())
                desc = 'The phpinfo()::upload_max_filesize is set to higher value (' + upload_max_filesize.group(1) + ').'
                v.set_desc(desc)
                kb.kb.append(self, 'phpinfo', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())
        ### [/upload_max_filesize] ###

        ### [upload_tmp_dir] ###
        regex_str = 'upload_tmp_dir</td><td class="v">(<i>no value</i>)</td>'
        upload_tmp_dir = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        if upload_tmp_dir:
            v = vuln.vuln()
            v.set_plugin_name(self.get_name())
            v.set_id(response.id)
            v.set_name('upload_tmp_dir:Everyone')
            v.set_severity(severity.LOW)
            v.set_url(response.get_url())
            desc = 'The phpinfo()::upload_tmp_dir may be set to world-accessible directory.'
            v.set_desc(desc)
            kb.kb.append(self, 'phpinfo', v)
            om.out.vulnerability(v.get_desc(), severity=v.get_severity())
        ### [/upload_tmp_dir] ###

        ##### [/Vulnerable Settings] #####
        ##### [Useful Informative Settings] #####
        ### [privilege] ###
        if lpt_flag == 'info':
            i = info.info()
            i.set_plugin_name(self.get_name())
            i.set_id(response.id)
            i.set_name(lpt_name)
            i.set_url(response.get_url())
            i.set_desc(lpt_desc)
            kb.kb.append(self, 'phpinfo', i)
            om.out.information(i.get_desc())
        ### [/privilege] ###

        ### [register_globals]###
        if rg_flag == 'info':
            i = info.info()
            i.set_plugin_name(self.get_name())
            i.set_id(response.id)
            i.set_name(rg_name)
            i.set_url(response.get_url())
            i.set_desc(rg_desc)
            kb.kb.append(self, 'phpinfo', i)
            om.out.information(i.get_desc())
        ### [/register_globals]###

        ### [enable_dl]###
        if ed_flag == 'info':
            i = info.info()
            i.set_plugin_name(self.get_name())
            i.set_id(response.id)
            i.set_name(ed_name)
            i.set_url(response.get_url())
            i.set_desc(ed_desc)
            kb.kb.append(self, 'phpinfo', i)
            om.out.information(i.get_desc())
        ### [/enable_dl]###

        ### [file_uploads] ###
        regex_str = 'file_uploads</td><td class="v">(On|<i>no value</i>)</td>'
        file_uploads = re.search(regex_str, response.get_body(), re.IGNORECASE)
        if file_uploads:
            i = info.info()
            i.set_plugin_name(self.get_name())
            i.set_id(response.id)
            i.set_name('file_uploads: On')
            i.set_url(response.get_url())
            desc = 'The phpinfo()::file_uploads is enabled.'
            i.set_desc(desc)
            kb.kb.append(self, 'phpinfo', i)
            om.out.information(i.get_desc())
        ### [/file_uploads] ###

        ### [magic_quotes_gpc] ###
        regex_str = 'magic_quotes_gpc</td><td class="v">(On|Off)</td>'
        magic_quotes_gpc = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        if magic_quotes_gpc:
            mqg = magic_quotes_gpc.group(1)
            i = info.info()
            i.set_plugin_name(self.get_name())
            i.set_id(response.id)
            i.set_url(response.get_url())
            if (mqg == 'On'):
                i.set_name('magic_quotes_gpc: On')
                desc = 'The phpinfo()::magic_quotes_gpc is on.'
            else:
                i.set_name('magic_quotes_gpc: Off')
                desc = 'The phpinfo()::magic_quotes_gpc is off.'
            i.set_desc(desc)
            kb.kb.append(self, 'phpinfo', i)
            om.out.information(i.get_desc())

        ### [/magic_quotes_gpc] ###

        ### [open_basedir] ###
        regex_str = 'open_basedir</td><td class="v">(.*?)</td>'
        open_basedir = re.search(regex_str, response.get_body(), re.IGNORECASE)

        if open_basedir:
            obd = open_basedir.group(1)
            i = info.info()
            i.set_plugin_name(self.get_name())
            i.set_id(response.id)
            i.set_url(response.get_url())

            if(obd == '<i>no value</i>'):
                i.set_name('open_basedir:disabled')
                desc = 'The phpinfo()::open_basedir is not set.'
                i.set_desc(desc)

            else:
                i.set_name('open_basedir:enabled')
                desc = 'The phpinfo()::open_basedir is set to ' + \
                    open_basedir.group(1) + '.'
                i.set_desc(desc)

        kb.kb.append(self, 'phpinfo', i)
        om.out.information(i.get_desc())
        ### [/open_basedir] ###

        ### [session_hash_function] ###
        regex_str = 'session\.hash_function</td><td class="v">(.*?)</td>'
        session_hash_function = re.search(
            regex_str, response.get_body(), re.IGNORECASE)
        if session_hash_function:
            i = info.info()
            i.set_plugin_name(self.get_name())
            i.set_id(response.id)
            i.set_url(response.get_url())
            if (session_hash_function.group(1) == 0 or session_hash_function.group(1) != 'no'):
                i.set_name('session.hash_function:md5')
                desc = 'The phpinfo()::session.hash_function use md5 algorithm.'
            else:
                i.set_name('session.hash_function:sha')
                desc = 'The phpinfo()::session.hash_function use sha algorithm.'

            i.set_desc(desc)
            kb.kb.append(self, 'phpinfo', i)
            om.out.information(i.get_desc())
        ### [/session_hash_function] ###

        ##### [/Useful Informative Settings] #####

    def _get_potential_phpinfos(self):
        '''
        @return: Filename of the php info file.
        '''
        res = []
        res.extend(
            ['phpinfo.php', 'PhpInfo.php', 'PHPinfo.php', 'PHPINFO.php'])
        res.extend(['phpInfo.php', 'info.php', 'test.php?mode=phpinfo'])
        res.extend(['index.php?view=phpinfo', 'index.php?mode=phpinfo'])
        res.extend(
            ['TEST.php?mode=phpinfo', '?mode=phpinfo', '?view=phpinfo'])
        res.extend(['install.php?mode=phpinfo', 'INSTALL.php?mode=phpinfo'])
        res.extend(
            ['admin.php?mode=phpinfo', 'phpversion.php', 'phpVersion.php'])
        res.extend(['test1.php', 'phpinfo1.php', 'phpInfo1.php', 'info1.php'])
        res.extend(['PHPversion.php', 'x.php', 'xx.php', 'xxx.php'])

        identified_os = kb.kb.get('fingerprint_os', 'operating_system_str')

        if not isinstance(identified_os, basestring):
            identified_os = cf.cf.get('target_os')

        if re.match('windows', identified_os, re.IGNORECASE):
            res = list(set([path.lower() for path in res]))

        return res

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
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
        '''
