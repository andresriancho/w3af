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
import core.data.kb.knowledgeBase as kb
import core.data.parsers.urlParser as urlParser
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
        self._analyzedDirs = []

    def discover(self, fuzzableRequest ):
        '''
        For every directory, fetch a list of files and analyze the response.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        dp = urlParser.getDomainPath( fuzzableRequest.getURL() )
        fuzzableRequestsToReturn = []
        
        if dp not in self._analyzedDirs:
            self._analyzedDirs.append( dp )
            # Init some variables
            self.is404 = kb.kb.getData( 'error404page', '404' )

        
            # Search for the web shells
            for webShellFilename in self._getWebShells():
                webShellUrl = urlParser.urlJoin(  dp , webShellFilename )
                response = self._urlOpener.GET( webShellUrl, useCache=True )
                
                if not webShellUrl.endswith(webShellFilename):
                    msg = 'It seems that you have hitted bug #1938087. We have been trying to reproduce it for a while'
                    msg += 'but it has been impossible for us. Please send a comment to '
                    msg += 'https://sourceforge.net/tracker/index.php?func=detail&aid=1938087&group_id=170274&atid=853652'
                    msg += 'With this information: \n'
                    msg += 'webShellUrl:' + webShellUrl + '\n'
                    msg += 'webShellFilename:' + webShellFilename + '\n'
                    msg += 'dp:' + dp + '\n'
                    print msg
                    om.out.error( msg )
        
                if not self.is404( response ):
                    v = vuln.vuln()
                    v.setId( response.id )
                    v.setName( 'Possible web backdoor' )
                    v.setSeverity(severity.HIGH)
                    v.setURL( response.getURL() )
                    v.setDesc( 'A web backdoor was found at: ' + v.getURL() + ' ; this could indicate that your server was hacked.' )
                    kb.kb.append( self, 'backdoors', v )
                    om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
                    
                    fuzzableRequestsToReturn.extend( self._createFuzzableRequests( response ) )
                    
        return fuzzableRequestsToReturn
    
    def _getWebShells( self ):
        '''
        @return: A list of filenames of common web shells and web backdoors.
        '''
        res = []
        # PHP
        res.extend( ['php-backdoor.php','simple-backdoor.php','cmd.php','phpshell.php','NCC-Shell.php'] )
        res.extend( ['ironshell.php','lamashell.php','load_shell.php','matamu.php','myshell.php','mysql.php','mysql_tool.php'] )
        res.extend( ['c99_w4cking.php','Crystal.php','ctt_sh.php','cybershell.php','Dx.php','gfs_sh.php','iMHaPFtp.php'] )
        res.extend( ['c99_PSych0.php','c99_madnet.php','c99_locus7s.php','c99.php','backupsql.php','accept_language.php'] )
        res.extend( ['pws.php','r57.php','r57_iFX.php','r57_kartal.php','r57_Mohajer22.php','rootshell.php','ru24_post_sh.php'] )
        res.extend( ['pHpINJ.php','PHPJackal.php','PHPRemoteView.php','Private-i3lue.php','php-include-w-shell.php'] )
        res.extend( ['PHANTASMA.php','nstview.php','nshell.php','NetworkFileManagerPHP.php'] )
        res.extend( ['simple_cmd.php','Uploader.php','zacosmall.php'] )
        
        # CGI / Perl
        res.extend( ['perlcmd.cgi','cmd.pl'] )
        
        # JSP
        res.extend( ['jsp-reverse.jsp','cmdjsp.jsp','cmd.jsp','cmd_win32.jsp','JspWebshell.jsp','JspWebshell1.2.jsp'] )
        
        # ASP
        res.extend( ['cmd.asp','cmdasp.aspx','cmdasp.asp','cmd-asp-5.1.asp','cmd.aspx','ntdaddy.asp'] )
        
        # Other
        res.extend( ['cmd.cfm','cfexec.cfm'] )
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
        This plugin searches for web shells in the directories that are sent as input. For example, if the input is:
            - http://localhost/w3af/webshells/f00b4r.php
            
        The plugin will perform these requests:
            - http://localhost/w3af/webshells/c99.php
            - http://localhost/w3af/webshells/cmd.php
            - http://localhost/w3af/webshells/webshell.php
            ...
        '''
