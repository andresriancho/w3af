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

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import w3afException

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity


class findBackdoor(baseDiscoveryPlugin):
    '''
    Find web backdoors and web shells.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._analyzed_dirs = []

    def discover(self, fuzzableRequest ):
        '''
        For every directory, fetch a list of shell files and analyze the response.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        domain_path = urlParser.getDomainPath( fuzzableRequest.getURL() )
        fuzzable_requests_to_return = []
        
        if domain_path not in self._analyzed_dirs:
            self._analyzed_dirs.append( domain_path )
            # Init some variables
            is_404 = kb.kb.getData( 'error404page', '404' )

            # Search for the web shells
            for web_shell_filename in self._get_web_shells():
                web_shell_url = urlParser.urlJoin(  domain_path , web_shell_filename )
                
                try:
                    response = self._urlOpener.GET( web_shell_url, useCache=True )
                except w3afException:
                    om.out.debug('Failed to GET webshell:' + web_shell_url)
                else:
                    if not is_404( response ):
                        v = vuln.vuln()
                        v.setId( response.id )
                        v.setName( 'Possible web backdoor' )
                        v.setSeverity(severity.HIGH)
                        v.setURL( response.getURL() )
                        msg = 'A web backdoor was found at: ' + v.getURL() + ' ; this could'
                        msg += ' indicate that your server was hacked.'
                        v.setDesc( msg )
                        kb.kb.append( self, 'backdoors', v )
                        om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
                        
                        fuzzable_requests = self._createFuzzableRequests( response )
                        fuzzable_requests_to_return.extend( fuzzable_requests )
                    
        return fuzzable_requests_to_return
    
    def _get_web_shells( self ):
        '''
        @return: A list of filenames of common web shells and web backdoors.
        '''
        res = []
        
        ## by aungkhant, Lists are taken from underground shell repositories and common sense
        
        # PHP
        res.extend( ['php-backdoor.php', 'simple-backdoor.php', 'cmd.php', 'phpshell.php'] )
        res.extend( ['NCC-Shell.php', 'mysql.php', 'mysql_tool.php', 'gfs_sh.php', 'iMHaPFtp.php'] )
        res.extend( ['ironshell.php', 'lamashell.php', 'load_shell.php', 'matamu.php'] )
        res.extend( ['c99_w4cking.php', 'Crystal.php', 'ctt_sh.php', 'cybershell.php', 'Dx.php'] )
        res.extend( ['c99_PSych0.php', 'c99_madnet.php', 'c99_locus7s.php', 'c99.php'] )
        res.extend( ['accept_language.php', 'rootshell.php', 'ru24_post_sh.php', 'zacosmall.php' ] )
        res.extend( ['pws.php', 'r57.php', 'r57_iFX.php', 'r57_kartal.php', 'r57_Mohajer22.php'] )
        res.extend( ['pHpINJ.php', 'PHPJackal.php', 'PHPRemoteView.php', 'Private-i3lue.php'] )
        res.extend( ['PHANTASMA.php', 'nstview.php', 'nshell.php', 'NetworkFileManagerPHP.php'] )
        res.extend( ['simple_cmd.php', 'Uploader.php', 'php-include-w-shell.php', 'backupsql.php'] )
        res.extend( ['myshell.php', 'c99shell.php'] )
        res.extend( ['c100.php', 'c100shell.php', 'locus7s.php', 'locus.php'] )
        res.extend( ['safe0ver.php','stresbypass.php','ekin0x.php','liz0zim.php'])
        res.extend( ['erne.php','spybypass.php','phpbypass.php','sosyete.php'])
        res.extend( ['remview.php','zaco.php','nst.php','heykir.php'])
        res.extend( ['simattacker.php','avent.php','fatal.php','dx.php'])
        res.extend( ['goonshell.php','safemod.php','unreal.php','w4k.php'])
        res.extend( ['winshell.php','mysql2.php','sql.php','jackal.php'])
        res.extend( ['dc.php','w4cking.php','x.php','xx.php','xxx.php'])
        res.extend( ['w3k.php','h4x.php','h4x0r.php','l33t.php'])
        res.extend( ['cod3r.php','cod3rzshell.php','cod3rz.php'])
        res.extend( ['locus.php','locu.php'])
        res.extend( ['jsback.php','worm.php','simp-worm_sys.p5.php'])
        res.extend( ['owned.php','0wn3d.php'])
        
        # CGI / Perl
        res.extend( ['perlcmd.cgi', 'cmd.pl'] )
        res.extend( ['shell.pl','cmd.cgi','shell.cgi'])
        
        # JSP
        res.extend( ['jsp-reverse.jsp', 'cmdjsp.jsp', 'cmd.jsp', 'cmd_win32.jsp'] )
        res.extend( ['JspWebshell.jsp', 'JspWebshell1.2.jsp'] )
        res.extend( ['shell.jsp'])
        res.extend( ['jsp-reverse.jspx', 'cmdjsp.jspx', 'cmd.jspx', 'cmd_win32.jspx'] )
        res.extend( ['JspWebshell.jspx', 'JspWebshell1.2.jspx'] )
        res.extend( ['shell.jspx'])
        res.extend( ['browser.jsp','cmd_win32.jsp'])
        res.extend( ['CmdServlet','cmdServlet','servlet/CmdServlet','servlet/cmdServlet'])
        
        # ASP
        res.extend( ['cmd.asp', 'cmdasp.aspx', 'cmdasp.asp', 'cmd-asp-5.1.asp', 'cmd.aspx'] )
        res.extend( ['ntdaddy.asp'] )        
        res.extend( ['ntdaddy.aspx','ntdaddy.mspx','cmd.mspx'] )
        res.extend( ['shell.asp','zehir4.asp','rhtools.asp','fso.asp'])
        res.extend( ['shell.aspx','zehir4.aspx','rhtools.aspx','fso.aspx'])
        res.extend( ['shell.mspx','zehir4.mspx','rhtools.mspx','fso.mspx'])
        res.extend( ['kshell.asp','aspydrv.asp','kacak.asp'])
        res.extend( ['kshell.aspx','aspydrv.aspx','kacak.aspx'])
        res.extend( ['kshell.mspx','aspydrv.mspx','kacak.mspx'])        
        
        # Other
        res.extend( ['cmd.cfm', 'cfexec.cfm'] )
        res.extend( ['shell.cfm','shell.do','shell.nsf','shell.d2w','shell.GPL'])
        res.extend( ['shell.show','shell.py'])
        res.extend( ['cmd.do','cmd.nsf','cmd.d2w','cmd.GPL'])
        res.extend( ['cmd.show','cmd.py'])
        res.extend( ['cmd.c','exploit.c','0wn3d.c'])
        res.extend( ['cmd.sh','cmd.js','shell.js'])
        return res

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []

    def getLongDesc( self ):
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
