"""
find_backdoors.py

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
import w3af.core.data.constants.severity as severity
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.vuln import Vuln

# By aungkhant. Lists are taken from underground shell repositories and
# common sense
WEB_SHELLS = (
    # PHP
    'php-backdoor.php', 'simple-backdoor.php', 'cmd.php', 'phpshell.php',
    'NCC-Shell.php', 'mysql.php', 'mysql_tool.php', 'gfs_sh.php', 'iMHaPFtp.php',
    'ironshell.php', 'lamashell.php', 'load_shell.php', 'matamu.php',
    'c99_w4cking.php', 'Crystal.php', 'ctt_sh.php', 'cybershell.php', 'Dx.php',
    'c99_PSych0.php', 'c99_madnet.php', 'c99_locus7s.php', 'c99.php',
    'accept_language.php', 'rootshell.php', 'ru24_post_sh.php', 'zacosmall.php',
    'pws.php', 'r57.php', 'r57_iFX.php', 'r57_kartal.php', 'r57_Mohajer22.php',
    'pHpINJ.php', 'PHPJackal.php', 'PHPRemoteView.php', 'Private-i3lue.php',
    'PHANTASMA.php', 'nstview.php', 'nshell.php', 'NetworkFileManagerPHP.php',
    'simple_cmd.php', 'Uploader.php', 'php-include-w-shell.php', 'backupsql.php',
    'myshell.php', 'c99shell.php',
    'c100.php', 'c100shell.php', 'locus7s.php', 'locus.php',
    'safe0ver.php', 'stresbypass.php', 'ekin0x.php', 'liz0zim.php',
    'erne.php', 'spybypass.php', 'phpbypass.php', 'sosyete.php',
    'remview.php', 'zaco.php', 'nst.php', 'heykir.php',
    'simattacker.php', 'avent.php', 'fatal.php', 'dx.php',
    'goonshell.php', 'safemod.php', 'unreal.php', 'w4k.php',
    'winshell.php', 'mysql2.php', 'sql.php', 'jackal.php',
    'dc.php', 'w4cking.php', 'x.php', 'xx.php', 'xxx.php',
    'w3k.php', 'h4x.php', 'h4x0r.php', 'l33t.php',
    'cod3r.php', 'cod3rzshell.php', 'cod3rz.php',
    'locus.php', 'locu.php',
    'jsback.php', 'worm.php', 'simp-worm_sys.p5.php',
    'owned.php', '0wn3d.php',
    # CGI / Perl
    'perlcmd.cgi', 'cmd.pl',
    'shell.pl', 'cmd.cgi', 'shell.cgi',
    # JSP
    'jsp-reverse.jsp', 'cmdjsp.jsp', 'cmd.jsp', 'cmd_win32.jsp',
    'JspWebshell.jsp', 'JspWebshell1.2.jsp',
    'shell.jsp',
    'jsp-reverse.jspx', 'cmdjsp.jspx', 'cmd.jspx', 'cmd_win32.jspx',
    'JspWebshell.jspx', 'JspWebshell1.2.jspx',
    'shell.jspx',
    'browser.jsp', 'cmd_win32.jsp',
    'CmdServlet', 'cmdServlet', 'servlet/CmdServlet', 'servlet/cmdServlet',
    'ListServlet', 'UpServlet',
    'up_win32.jsp',
    # ASP
    'cmd.asp', 'cmdasp.aspx', 'cmdasp.asp', 'cmd-asp-5.1.asp', 'cmd.aspx',
    'ntdaddy.asp',
    'ntdaddy.aspx', 'ntdaddy.mspx', 'cmd.mspx',
    'shell.asp', 'zehir4.asp', 'rhtools.asp', 'fso.asp',
    'shell.aspx', 'zehir4.aspx', 'rhtools.aspx', 'fso.aspx',
    'shell.mspx', 'zehir4.mspx', 'rhtools.mspx', 'fso.mspx',
    'kshell.asp', 'aspydrv.asp', 'kacak.asp',
    'kshell.aspx', 'aspydrv.aspx', 'kacak.aspx',
    'kshell.mspx', 'aspydrv.mspx', 'kacak.mspx',
    # Other
    'cmd.cfm', 'cfexec.cfm',
    'shell.cfm', 'shell.do', 'shell.nsf', 'shell.d2w', 'shell.GPL',
    'shell.show', 'shell.py',
    'cmd.do', 'cmd.nsf', 'cmd.d2w', 'cmd.GPL',
    'cmd.show', 'cmd.py',
    'cmd.c', 'exploit.c', '0wn3d.c',
    'cmd.sh', 'cmd.js', 'shell.js',
    'list.sh', 'up.sh', 'nc.exe', 'netcat.exe', 'socat.exe', 'cmd.pl')

# Mapping object to use in XPath search
BACKDOOR_COLLECTION = {
    'input': {'value': ('run', 'send', 'exec', 'execute', 'run cmd',
                        'execute command', 'run command', 'list', 'connect'),
              'name': ('cmd', 'command')},
    'form': {'enctype': ('multipart/form-data',)}
}

# List of known offensive words.
KNOWN_OFFENSIVE_WORDS = set(
    ('access', 'backdoor', 'cmd', 'cmdExe_Click', 'cmd_exec',
                           'command', 'connect', 'directory', 'directories', 'exec',
                           'exec_cmd', 'execute', 'eval', 'file', 'file upload', 'hack', 'hacked',
                           'hacked by', 'hacking', 'htaccess', 'launch command', 'launch shell',
                           'list', 'listing', 'output', 'passwd', 'password', 'permission',
                           'remote', 'reverse', 'run', 'runcmd', 'server', 'shell',
                           'socket', 'system', 'user', 'userfile', 'userid', 'web shell',
                           'webshell'))


class find_backdoors(CrawlPlugin):
    """
    Find web backdoors and web shells.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._analyzed_dirs = ScalableBloomFilter()

    def crawl(self, fuzzable_request):
        """
        For every directory, fetch a list of shell files and analyze the response.

        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        domain_path = fuzzable_request.get_url().get_domain_path()

        if domain_path not in self._analyzed_dirs:
            self._analyzed_dirs.add(domain_path)

            #   Send the requests using threads:
            self.worker_pool.map(self._check_if_exists,
                                    (domain_path.url_join(
                                        fname) for fname in WEB_SHELLS)
                                    )

    def _check_if_exists(self, web_shell_url):
        """
        Check if the file exists.

        :param web_shell_url: The URL to check
        """
        try:
            response = self._uri_opener.GET(web_shell_url, cache=True)
        except BaseFrameworkException:
            om.out.debug('Failed to GET webshell:' + web_shell_url)
        else:
            if self._is_possible_backdoor(response):
                desc = 'A web backdoor was found at: "%s"; this could ' \
                       'indicate that the server has been compromised.'
                desc = desc % response.get_url()
                
                v = Vuln('Potential web backdoor', desc, severity.HIGH,
                         response.id, self.get_name())
                v.set_url(response.get_url())
                
                kb.kb.append(self, 'backdoors', v)
                om.out.vulnerability(v.get_desc(), severity=v.get_severity())

                for fr in self._create_fuzzable_requests(response):
                    self.output_queue.put(fr)

    def _is_possible_backdoor(self, response):
        """
        Heuristic to infer if the content of <response> has the pattern of a
        backdoor response.

        :param response: HTTPResponse object
        :return: A bool value
        """
        if not is_404(response):
            body_text = response.get_body()
            dom = response.get_dom()
            if dom is not None:
                for ele, attrs in BACKDOOR_COLLECTION.iteritems():
                    for attrname, attr_vals in attrs.iteritems():
                        # Set of lowered attribute values
                        dom_attr_vals = \
                            set(n.get(attrname).lower() for n in
                                (dom.xpath('//%s[@%s]' % (ele, attrname))))
                        # If at least one elem in intersection return True
                        if (dom_attr_vals and set(attr_vals)):
                            return True

            # If no regex matched then try with keywords. At least 2 should be
            # contained in 'body_text' to succeed.
            times = 0
            for back_kw in KNOWN_OFFENSIVE_WORDS:
                if re.search(back_kw, body_text, re.I):
                    times += 1
                    if times == 2:
                        return True
        return False

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin searches for web shells in the directories that are sent as input.
        For example, if the input is:
            - http://host.tld/w3af/f00b4r.php

        The plugin will perform these requests:
            - http://host.tld/w3af/c99.php
            - http://host.tld/w3af/cmd.php
            - http://host.tld/w3af/webshell.php
            ...
        """
