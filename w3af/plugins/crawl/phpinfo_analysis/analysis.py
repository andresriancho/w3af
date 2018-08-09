"""
analysis.py

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

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info import Info


def register_globals(response):
    regex_str = 'register_globals</td><td class="v">(On|Off)</td>'
    register_globals_mo = re.search(regex_str, response.get_body(), re.I)

    if not register_globals_mo:
        return
    
    rg = register_globals_mo.group(1)
    if rg == 'On':
        desc = 'The phpinfo()::register_globals is on.'
        v = Vuln('PHP register_globals: On', desc,
                 severity.MEDIUM, response.id, 'phpinfo')
        v.set_url(response.get_url())

        kb.kb.append('phpinfo', 'phpinfo', v)
        om.out.vulnerability(v.get_desc(), severity=v.get_severity())
    else:
        rg_name = 'PHP register_globals: Off'
        rg_desc = 'The phpinfo()::register_globals is off.'
        i = Info(rg_name, rg_desc, response.id, 'phpinfo')
        i.set_url(response.get_url())

        kb.kb.append('phpinfo', 'phpinfo', i)
        om.out.information(i.get_desc())


def allow_url_fopen(response):
    regex_str = 'allow_url_fopen</td><td class="v">(On|<i>no value</i>)</td>'
    allow_url_fopen_mo = re.search(regex_str, response.get_body(), re.I)

    if not allow_url_fopen_mo:
        return

    desc = 'The phpinfo()::allow_url_fopen is enabled.'
    v = Vuln('PHP allow_url_fopen: On', desc,
             severity.MEDIUM, response.id, 'phpinfo')
    v.set_url(response.get_url())

    kb.kb.append('phpinfo', 'phpinfo', v)
    om.out.vulnerability(v.get_desc(), severity=v.get_severity())


def allow_url_include(response):
    regex_str = 'allow_url_include</td><td class="v">(On|<i>no value</i>)</td>'
    allow_url_include_mo = re.search(regex_str, response.get_body(), re.I)

    if not allow_url_include_mo:
        return

    desc = 'The phpinfo()::allow_url_include is enabled.'
    v = Vuln('PHP allow_url_include: On', desc,
             severity.MEDIUM, response.id, 'phpinfo')
    v.set_url(response.get_url())

    kb.kb.append('phpinfo', 'phpinfo', v)
    om.out.vulnerability(v.get_desc(), severity=v.get_severity())


def display_errors(response):
    regex_str = 'display_errors</td><td class="v">(On|<i>no value</i>)</td>'
    display_errors_mo = re.search(regex_str, response.get_body(), re.I)

    if not display_errors_mo:
        return

    desc = 'The phpinfo()::display_errors is enabled.'
    v = Vuln('PHP display_errors: On', desc,
             severity.MEDIUM, response.id, 'phpinfo')
    v.set_url(response.get_url())

    kb.kb.append('phpinfo', 'phpinfo', v)
    om.out.vulnerability(v.get_desc(), severity=v.get_severity())


def expose_php(response):
    regex_str = 'expose_php</td><td class="v">(On|<i>no value</i>)</td>'
    expose_php_mo = re.search(regex_str, response.get_body(), re.I)

    if not expose_php_mo:
        return

    desc = 'The phpinfo()::expose_php is enabled.'
    v = Vuln('PHP expose_php: On', desc,
             severity.MEDIUM, response.id, 'phpinfo')
    v.set_url(response.get_url())

    kb.kb.append('phpinfo', 'phpinfo', v)
    om.out.vulnerability(v.get_desc(), severity=v.get_severity())


def lowest_privilege_test(response):
    regex_str = 'User/Group </td><td class="v">(.*?)\((\d.*?)\)/(\d.*?)</td>'
    lowest_privilege_test_mo = re.search(regex_str, response.get_body(), re.I)

    if not lowest_privilege_test_mo:
        return

    lpt_uname = lowest_privilege_test_mo.group(1)

    lpt_uid = lowest_privilege_test_mo.group(2)
    lpt_uid = int(lpt_uid)

    lpt_gid = lowest_privilege_test_mo.group(3)
    lpt_gid = int(lpt_gid)

    is_privileged_username_mo = re.match('root|apache|daemon|bin|operator|adm', lpt_uname, re.I)

    if lpt_uid < 99 or lpt_gid < 99 or is_privileged_username_mo:

        desc = ('phpinfo()::PHP may be executing as a higher privileged'
                ' user or group. Username: %s, User id: %s, Group id: %s.')
        desc %= (lpt_uname, lpt_uid, lpt_gid)

        v = Vuln('PHP running with privileged user', desc,
                 severity.MEDIUM, response.id, 'phpinfo')
        v.set_url(response.get_url())

        kb.kb.append('phpinfo', 'phpinfo', v)
        om.out.vulnerability(v.get_desc(), severity=v.get_severity())
    else:
        desc = ('PHP seems to be running as a low privileged user.'
                ' Username: %s, User id: %s, Group id: %s.')

        desc %= (lpt_uname, lpt_uid, lpt_gid)

        i = Info('PHP running as low privileged user', desc, response.id, 'phpinfo')
        i.set_url(response.get_url())

        kb.kb.append('phpinfo', 'phpinfo', i)
        om.out.information(i.get_desc())


def disable_functions(response):
    regex_str = 'disable_functions</td><td class="v">(.*?)</td>'
    disable_functions_mo = re.search(regex_str, response.get_body(), re.I)

    if not disable_functions_mo:
        return

    secure_df = 8
    df = disable_functions_mo.group(1)
    dfe = df.split(',')

    if len(dfe) >= secure_df:
        return

    desc = ('The phpinfo()::disable_functions does NOT seem to be set. This'
            ' configuration parameter is a good indicator of a security'
            '-enabled PHP installation. The disabled functions are: %s')
    desc %= (', '.join(dfe),)

    v = Vuln('PHP disable_functions weakness', desc,
             severity.MEDIUM, response.id, 'phpinfo')
    v.set_url(response.get_url())

    kb.kb.append('phpinfo', 'phpinfo', v)
    om.out.vulnerability(v.get_desc(), severity=v.get_severity())


def curl_file_support(response):
    regex_str = '<h1 class="p">PHP Version (\d).(\d).(\d)</h1>'
    curl_file_support_mo = re.search(regex_str, response.get_body(), re.I)

    if not curl_file_support_mo:
        return

    php_major_ver = curl_file_support_mo.group(1)
    php_minor_ver = curl_file_support_mo.group(2)
    php_rev_ver = curl_file_support_mo.group(3)

    current_ver = php_major_ver + '.' + php_minor_ver + php_rev_ver
    current_ver = float(current_ver)
    php_major_ver = int(php_major_ver)

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
        desc = ('The phpinfo()::cURL::file_support has a security hole'
                ' present in this version of PHP allows the cURL'
                ' functions to bypass safe_mode and open_basedir'
                ' restrictions.')
        v = Vuln('PHP curl_file_support:not_fixed', desc,
                 severity.MEDIUM, response.id, 'phpinfo')
        v.set_url(response.get_url())

        kb.kb.append('phpinfo', 'phpinfo', v)
        om.out.vulnerability(v.get_desc(), severity=v.get_severity())


def cgi_force_redirect(response):
    regex_str = 'cgi_force_redirect</td><td class="v">(.*?)</td>'
    cgi_force_redirect_mo = re.search(regex_str, response.get_body(), re.I)

    if not cgi_force_redirect_mo:
        return

    utd = cgi_force_redirect_mo.group(1)
    if utd == 'On':
        return

    desc = 'The phpinfo()::CGI::force_redirect is disabled.'
    v = Vuln('PHP cgi_force_redirect: Off', desc,
             severity.MEDIUM, response.id, 'phpinfo')
    v.set_url(response.get_url())

    kb.kb.append('phpinfo', 'phpinfo', v)
    om.out.vulnerability(v.get_desc(), severity=v.get_severity())


def session_cookie_httponly(response):
    regex_str = 'session\.cookie_httponly</td><td class="v">(Off|no|0)</td>'
    session_cookie_httponly_mo = re.search(regex_str, response.get_body(), re.I)

    if not session_cookie_httponly_mo:
        return

    desc = 'The phpinfo()::session.cookie_httponly is off.'
    v = Vuln('PHP session.cookie_httponly: Off', desc,
             severity.MEDIUM, response.id, 'phpinfo')
    v.set_url(response.get_url())

    kb.kb.append('phpinfo', 'phpinfo', v)
    om.out.vulnerability(v.get_desc(), severity=v.get_severity())


def session_save_path(response):
    regex_str = 'session\.save_path</td><td class="v">(<i>no value</i>)</td>'
    session_save_path_mo = re.search(regex_str, response.get_body(), re.I)

    if not session_save_path_mo:
        return

    desc = ('The phpinfo()::session.save_path may be set to a world-'
            'readable directory.')
    v = Vuln('Word readable PHP session_save_path', desc,
             severity.LOW, response.id, 'phpinfo')
    v.set_url(response.get_url())

    kb.kb.append('phpinfo', 'phpinfo', v)
    om.out.vulnerability(v.get_desc(), severity=v.get_severity())


def session_use_trans(response):
    regex_str = 'session\.use_trans</td><td class="v">(On)</td>'
    session_use_trans_mo = re.search(regex_str, response.get_body(), re.I)

    if not session_use_trans_mo:
        return

    desc = ('The phpinfo()::session.use_trans is enabled. This makes'
            ' session hijacking easier.')
    v = Vuln('PHP session_use_trans: On', desc,
             severity.MEDIUM, response.id, 'phpinfo')
    v.set_url(response.get_url())

    kb.kb.append('phpinfo', 'phpinfo', v)
    om.out.vulnerability(v.get_desc(), severity=v.get_severity())


def default_charset(response):
    regex_str = 'default_charset</td><td class="v">(Off|no|0)</td>'
    default_charset_mo = re.search(regex_str, response.get_body(), re.I)

    if not default_charset_mo:
        return

    desc = ('The phpinfo()::default_charset is set to none. This'
            ' makes PHP scripts vulnerable to various charset'
            ' encoding XSS.')
    v = Vuln('PHP default_charset: Off', desc,
             severity.MEDIUM, response.id, 'phpinfo')
    v.set_url(response.get_url())

    kb.kb.append('phpinfo', 'phpinfo', v)
    om.out.vulnerability(v.get_desc(), severity=v.get_severity())


def enable_dl(response):
    regex_str = 'enable_dl</td><td class="v">(On|Off)</td>'
    enable_dl_mo = re.search(regex_str, response.get_body(), re.I)

    if not enable_dl_mo:
        return

    rg = enable_dl_mo.group(1)
    if rg == 'On':
        desc = 'The phpinfo()::enable_dl is on.'
        v = Vuln('PHP enable_dl: On', desc,
                 severity.MEDIUM, response.id, 'phpinfo')
        v.set_url(response.get_url())

        kb.kb.append('phpinfo', 'phpinfo', v)
        om.out.vulnerability(v.get_desc(), severity=v.get_severity())
    else:
        ed_name = 'PHP enable_dl: Off'
        ed_desc = 'The phpinfo()::enable_dl is off.'
        i = Info(ed_name, ed_desc, response.id, 'phpinfo')
        i.set_url(response.get_url())

        kb.kb.append('phpinfo', 'phpinfo', i)
        om.out.information(i.get_desc())


def memory_limit(response):
    regex_str = 'memory_limit</td><td class="v">(\d.*?)</td>'
    memory_limit_mo = re.search(regex_str, response.get_body(), re.I)

    if not memory_limit_mo:
        return

    secure_ml = 10

    ml = memory_limit_mo.group(1) + ''
    ml = ml.replace('M', '')
    ml = int(ml)

    if ml > secure_ml:
        desc = 'The phpinfo()::memory_limit is set to a high value: %s'
        desc %= (memory_limit_mo.group(1),)

        v = Vuln('PHP high memory limit', desc,
                 severity.MEDIUM, response.id, 'phpinfo')
        v.set_url(response.get_url())

        kb.kb.append('phpinfo', 'phpinfo', v)
        om.out.vulnerability(v.get_desc(), severity=v.get_severity())


def post_max_size(response):
    regex_str = 'post_max_size</td><td class="v">(\d.*?)</td>'
    post_max_size_mo = re.search(regex_str, response.get_body(), re.IGNORECASE)

    if not post_max_size_mo:
        return

    secure_pms = 20
    pms = post_max_size_mo.group(1) + ''
    pms = pms.replace('M', '')
    pms = int(pms)

    if pms <= secure_pms:
        return

    desc = 'The phpinfo()::post_max_size is set to a high value: %s'
    desc %= (post_max_size_mo.group(1),)

    v = Vuln('PHP high POST max size', desc,
             severity.LOW, response.id, 'phpinfo')
    v.set_url(response.get_url())

    kb.kb.append('phpinfo', 'phpinfo', v)
    om.out.vulnerability(v.get_desc(), severity=v.get_severity())


def upload_max_filesize(response):
    regex_str = 'upload_max_filesize</td><td class="v">(\d.*?)</td>'
    upload_max_filesize_mo = re.search(regex_str, response.get_body(), re.IGNORECASE)

    if not upload_max_filesize_mo:
        return

    secure_umf = 20
    umf = upload_max_filesize_mo.group(1) + ''
    umf = umf.replace('M', '')
    umf = int(umf)

    if umf <= secure_umf:
        return

    desc = 'The phpinfo()::upload_max_filesize is set to a high value: %s'
    desc %= (upload_max_filesize_mo.group(1),)

    v = Vuln('PHP upload_max_filesize:high', desc,
             severity.LOW, response.id, 'phpinfo')
    v.set_url(response.get_url())

    kb.kb.append('phpinfo', 'phpinfo', v)
    om.out.vulnerability(v.get_desc(), severity=v.get_severity())


def upload_tmp_dir(response):
    regex_str = 'upload_tmp_dir</td><td class="v">(<i>no value</i>)</td>'
    upload_tmp_dir_mo = re.search(regex_str, response.get_body(), re.I)

    if not upload_tmp_dir_mo:
        return

    desc = 'The phpinfo()::upload_tmp_dir may be set to world-readable directory.'
    v = Vuln('PHP upload_tmp_dir is world readable', desc,
             severity.LOW, response.id, 'phpinfo')
    v.set_url(response.get_url())

    kb.kb.append('phpinfo', 'phpinfo', v)
    om.out.vulnerability(v.get_desc(), severity=v.get_severity())


def file_uploads(response):
    regex_str = 'file_uploads</td><td class="v">(On|<i>no value</i>)</td>'
    file_uploads_mo = re.search(regex_str, response.get_body(), re.IGNORECASE)

    if not file_uploads_mo:
        return

    desc = 'The phpinfo()::file_uploads is enabled.'
    i = Info('PHP file_uploads: On', desc, response.id, 'phpinfo')
    i.set_url(response.get_url())

    kb.kb.append('phpinfo', 'phpinfo', i)
    om.out.information(i.get_desc())


def magic_quotes_gpc(response):
    regex_str = 'magic_quotes_gpc</td><td class="v">(On|Off)</td>'
    magic_quotes_gpc_mo = re.search(regex_str, response.get_body(), re.I)

    if not magic_quotes_gpc_mo:
        return

    mqg = magic_quotes_gpc_mo.group(1)

    if mqg == 'On':
        desc = 'The phpinfo()::magic_quotes_gpc is on.'
        i = Info('PHP magic_quotes_gpc: On', desc, response.id,
                 'phpinfo')

    else:
        desc = 'The phpinfo()::magic_quotes_gpc is off.'
        i = Info('PHP magic_quotes_gpc: Off', desc, response.id,
                 'phpinfo')

    i.set_url(response.get_url())
    kb.kb.append('phpinfo', 'phpinfo', i)
    om.out.information(i.get_desc())


def open_basedir(response):
    regex_str = 'open_basedir</td><td class="v">(.*?)</td>'
    open_basedir_mo = re.search(regex_str, response.get_body(), re.I)

    if not open_basedir_mo:
        return

    obd = open_basedir_mo.group(1)

    if obd == '<i>no value</i>':
        desc = 'The phpinfo()::open_basedir is not set.'
        i = Info('PHP open_basedir:disabled', desc, response.id,
                 'phpinfo')

    else:
        desc = 'The phpinfo()::open_basedir is set to %s.'
        desc %= open_basedir_mo.group(1)
        i = Info('PHP open_basedir:enabled', desc, response.id,
                 'phpinfo')

    i.set_url(response.get_url())
    kb.kb.append('phpinfo', 'phpinfo', i)
    om.out.information(i.get_desc())


def session_hash_function(response):
    regex_str = 'session\.hash_function</td><td class="v">(.*?)</td>'
    session_hash_function_mo = re.search(regex_str, response.get_body(), re.I)

    if not session_hash_function_mo:
        return

    if session_hash_function_mo.group(1) == 0 \
            or session_hash_function_mo.group(1) != 'no':
        desc = 'The phpinfo()::session.hash_function uses the insecure md5 algorithm.'
        i = Info('PHP session.hash_function:md5', desc, response.id,
                 'phpinfo')
    else:
        desc = 'The phpinfo()::session.hash_function uses the insecure sha algorithm.'
        i = Info('PHP session.hash_function:sha', desc, response.id,
                 'phpinfo')

    i.set_url(response.get_url())

    kb.kb.append('phpinfo', 'phpinfo', i)
    om.out.information(i.get_desc())
