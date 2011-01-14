'''
findBackdoor.py

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

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.data.db.temp_persist import disk_list

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.coreHelpers.fingerprint_404 import is_404
from core.controllers.w3afException import w3afException

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

# By aungkhant. Lists are taken from underground shell repositories and
# common sense

WEB_SHELLS = (
    # PHP
    'php-backdoor.php', 'simple-backdoor.php', 'cmd.php', 'phpshell.php',
    'NCC-Shell.php', 'mysql.php', 'mysql_tool.php', 'gfs_sh.php', 'iMHaPFtp.php',
    'ironshell.php', 'lamashell.php', 'load_shell.php', 'matamu.php',
    'c99_w4cking.php', 'Crystal.php', 'ctt_sh.php', 'cybershell.php', 'Dx.php',
    'c99_PSych0.php', 'c99_madnet.php', 'c99_locus7s.php', 'c99.php',
    'accept_language.php', 'rootshell.php', 'ru24_post_sh.php', 'zacosmall.php' ,
    'pws.php', 'r57.php', 'r57_iFX.php', 'r57_kartal.php', 'r57_Mohajer22.php',
    'pHpINJ.php', 'PHPJackal.php', 'PHPRemoteView.php', 'Private-i3lue.php',
    'PHANTASMA.php', 'nstview.php', 'nshell.php', 'NetworkFileManagerPHP.php',
    'simple_cmd.php', 'Uploader.php', 'php-include-w-shell.php', 'backupsql.php',
    'myshell.php', 'c99shell.php',
    'c100.php', 'c100shell.php', 'locus7s.php', 'locus.php',
    'safe0ver.php','stresbypass.php','ekin0x.php','liz0zim.php',
    'erne.php','spybypass.php','phpbypass.php','sosyete.php',
    'remview.php','zaco.php','nst.php','heykir.php',
    'simattacker.php','avent.php','fatal.php','dx.php',
    'goonshell.php','safemod.php','unreal.php','w4k.php',
    'winshell.php','mysql2.php','sql.php','jackal.php',
    'dc.php','w4cking.php','x.php','xx.php','xxx.php',
    'w3k.php','h4x.php','h4x0r.php','l33t.php',
    'cod3r.php','cod3rzshell.php','cod3rz.php',
    'locus.php','locu.php',
    'jsback.php','worm.php','simp-worm_sys.p5.php',
    'owned.php','0wn3d.php',
    # CGI / Perl
    'perlcmd.cgi', 'cmd.pl',
    'shell.pl','cmd.cgi','shell.cgi',
    # JSP
    'jsp-reverse.jsp', 'cmdjsp.jsp', 'cmd.jsp', 'cmd_win32.jsp',
    'JspWebshell.jsp', 'JspWebshell1.2.jsp',
    'shell.jsp',
    'jsp-reverse.jspx', 'cmdjsp.jspx', 'cmd.jspx', 'cmd_win32.jspx',
    'JspWebshell.jspx', 'JspWebshell1.2.jspx',
    'shell.jspx',
    'browser.jsp','cmd_win32.jsp',
    'CmdServlet','cmdServlet','servlet/CmdServlet','servlet/cmdServlet',
    'ListServlet','UpServlet',
    'up_win32.jsp',
    # ASP
    'cmd.asp', 'cmdasp.aspx', 'cmdasp.asp', 'cmd-asp-5.1.asp', 'cmd.aspx',
    'ntdaddy.asp',        
    'ntdaddy.aspx','ntdaddy.mspx','cmd.mspx',
    'shell.asp','zehir4.asp','rhtools.asp','fso.asp',
    'shell.aspx','zehir4.aspx','rhtools.aspx','fso.aspx',
    'shell.mspx','zehir4.mspx','rhtools.mspx','fso.mspx',
    'kshell.asp','aspydrv.asp','kacak.asp',
    'kshell.aspx','aspydrv.aspx','kacak.aspx',
    'kshell.mspx','aspydrv.mspx','kacak.mspx',
    # Other
    'cmd.cfm', 'cfexec.cfm',
    'shell.cfm','shell.do','shell.nsf','shell.d2w','shell.GPL',
    'shell.show','shell.py',
    'cmd.do','cmd.nsf','cmd.d2w','cmd.GPL',
    'cmd.show','cmd.py',
    'cmd.c','exploit.c','0wn3d.c',
    'cmd.sh','cmd.js','shell.js',        
    'list.sh','up.sh','nc.exe','netcat.exe','socat.exe','cmd.pl')

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


class findBackdoor(baseDiscoveryPlugin):
    '''
    Find web backdoors and web shells.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._analyzed_dirs = disk_list()
        self._fuzzable_requests_to_return = []

    def discover(self, fuzzableRequest):
        '''
        For every directory, fetch a list of shell files and analyze the response.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains 
        (among other things) the URL to test.
        '''
        domain_path = fuzzableRequest.getURL().getDomainPath()
        self._fuzzable_requests_to_return = []

        if domain_path not in self._analyzed_dirs:
            self._analyzed_dirs.append(domain_path)

            # Search for the web shells
            for web_shell_filename in WEB_SHELLS:
                web_shell_url = domain_path.urlJoin(web_shell_filename)
                # Perform the check in different threads
                targs = (web_shell_url,)
                self._tm.startFunction(target=self._check_if_exists, 
                                       args=targs, ownerObj=self)

            # Wait for all threads to finish
            self._tm.join(self)

            return self._fuzzable_requests_to_return

    
    def _check_if_exists(self, web_shell_url):
        '''
        Check if the file exists.
        
        @parameter web_shell_url: The URL to check
        '''
        try:
            response = self._urlOpener.GET(web_shell_url, useCache=True)
        except w3afException:
            om.out.debug('Failed to GET webshell:' + web_shell_url)
        else:
            if self._is_possible_backdoor(response):
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setId(response.id)
                v.setName('Possible web backdoor')
                v.setSeverity(severity.HIGH)
                v.setURL(response.getURL())
                msg = 'A web backdoor was found at: "%s"; this could ' \
                'indicate that the server was hacked.' % v.getURL()
                v.setDesc(msg)
                kb.kb.append(self, 'backdoors', v)
                om.out.vulnerability(v.getDesc(), severity=v.getSeverity())

                fuzzable_requests = self._createFuzzableRequests(response)
                self._fuzzable_requests_to_return += fuzzable_requests
            
    def _is_possible_backdoor(self, response):
        '''
        Heuristic to infer if the content of <response> has the pattern of a
        backdoor response.
        
        @param response: httpResponse object
        @return: A bool value
        '''
        if not is_404(response):
            body_text = response.getBody()
            dom  = response.getDOM()
            if dom:
                for ele, attrs in BACKDOOR_COLLECTION.iteritems():
                    for attrname, attr_vals in attrs.iteritems():
                        # Set of lowered attribute values
                        dom_attr_vals = \
                            set(n.get(attrname).lower() for n in \
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

    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = optionList()
        return ol

    def setOptions(self, OptionList):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        '''
        pass

    def getPluginDeps(self):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []

    def getLongDesc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin searches for web shells in the directories that are sent as input.
        For example, if the input is:
            - http://host.tld/w3af/f00b4r.php
            
        The plugin will perform these requests:
            - http://host.tld/w3af/c99.php
            - http://host.tld/w3af/cmd.php
            - http://host.tld/w3af/webshell.php
            ...
        '''
