'''
googleProxy.py

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
from core.controllers.w3afException import w3afException
from core.controllers.daemons.proxy import *

import cgi , urllib
import core.data.kb.knowledgeBase as kb
from core.data.kb.proxy import proxy as kbProxy

import re
import core.data.constants.w3afPorts as w3afPorts

class googleProxy(baseAttackPlugin):
    '''
    A local proxy for HTTP requests that uses Google to relay requests.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseAttackPlugin.__init__(self)
        
        # Internal variables
        self._proxyd = None
        
        # User options
        self._proxyAddress = '127.0.0.1'
        self._proxyPort = w3afPorts.GOOGLEPROXY
    
    def setUrlOpener( self, urlOpener ):
        self._urlOpener = urlOpener
    
    def exploit( self, vulnToExploit=None ):
        '''
        Do nothing, this plugin is rather odd.
        This plugin is a  googleProxy server that's used for mangling requests. All the "magic" is done
        in the _proxy method and in the handler class.
        '''
        
        om.out.information('google proxy listening on ' + self._proxyAddress + ':' + str(self._proxyPort) )

        # Now, I'm starting the proxy server !
        self._proxy()
        
        kbp = kbProxy(self._proxyd)
        
        # Save the proxy object to the kb
        kb.kb.append( self, 'proxy', kbp )
        
        return [kbp,]
        
    def canExploit( self, vulnToExploit=None ):
        '''
        Overwrites the default canExploit, I don't really need to define the method: getVulnName2Exploit( self )
        '''
        return True
        
    def getAttackType(self):
        return 'proxy'
    
    def fastExploit( self ):
        self.exploit()
    
    def getRootProbability( self ):
        return 0.0
        
    def setOptions( self, OptionsMap ):
        
        self._proxyPort = OptionsMap['proxyPort']
        self._proxyAddress = OptionsMap['proxyAddress']
        
        # Restart the proxy, with the new options
        self._proxy()
    
    class proxyHandler(w3afProxyHandler):
        
        def _editResponse( self, responseBody ):
            #responseBody = responseBody.replace('/gwt/n?u=http%3A%2F%2F', 'http://')
            responseBody = responseBody.replace( '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE html PUBLIC "-//WAPFORUM//DTD XHTML Mobile 1.0//EN" "http://www.wapforum.org/DTD/xhtml-mobile10.dtd">', '')
            responseBody = responseBody.replace('<html xmlns="http://www.w3.org/1999/xhtml">', '<html>')
            responseBody = responseBody.replace('&amp;_gwt_noimg=1', '')
            responseBody = responseBody.replace('&amp;_gwt_srcpg=0', '')
            responseBody = responseBody.replace('&amp;_gwt_ov=1', '')
            responseBody = re.sub('<div style="background-color:#9ACEFF"><hr/>P.*', '</html>', responseBody)
            responseBody = re.sub('<div style="background-color:#9ACEFF"><a href=".*?">.*?</a><br/><hr/></div>', '', responseBody)
            for match in re.findall( '/gwt/n\?u=(.*?)"', responseBody ):
                responseBody = responseBody.replace( '/gwt/n?u=' + match, urllib.unquote_plus( match ), 1)
            return responseBody
        
        def _sendToBrowser( self, res ):
            '''
            Send a response to the browser
            '''
            # return the response to the browser
            try:
                self.send_response( res.getCode() )
                
                for header in res.getHeaders():
                    if not header == 'content-type':
                        self.send_header( header, res.getHeaders()[header] )
                    else:
                        self.send_header( 'content-type', 'text/html' )
                self.send_header( 'Connection', 'close')
                self.end_headers()
                
                self.wfile.write( self._editResponse( res.getBody() ) )
                self.wfile.close()
            except Exception, e:
                om.out.debug('Failed to send the data to the browser: ' + str(e) )      
    
        def _sendToServer( self ):
            '''
            I should send to the server:
                -   http://www.google.com/gwt/n?u=http%3A%2F%2Fwww.joomla.org%2F&_gwt_noimg=1
            When the client requests:
                -   http://www.joomla.org
            '''
            self.headers['Connection'] = 'close'
            
            # Prepare the url for google.
            googleProxyURL = 'http://www.google.com/gwt/n?'
            qs = queryString.queryString()
            qs['u'] = self.path
            qs['_gwt_noimg'] = 1
            url = googleProxyURL + str( qs )
            
            # Do the request to the remote server
            if self.headers.dict.has_key('content-length'):
                # POST
                cl = int( self.headers['content-length'] )
                postData = self.rfile.read( cl )
                try:
                    res = self._urlOpener.POST( url , data=postData, headers=self.headers )
                except w3afException, w:
                    om.out.error('The proxy request failed, error: ' + str(w) )
                    raise w
                except:
                    raise
                return res
                
            else:
                # GET
                try:
                    res = self._urlOpener.GET( url, headers=self.headers )
                except w3afException, w:
                    om.out.error('The proxy request failed, error: ' + str(w) )
                    raise w
                except:
                    raise
                return res

            
    def _proxy( self ):
        '''
        This method starts the proxy server with the configured options.
        '''
        if self._proxyd != None and self._proxyd.isRunning():
            self._proxyd.stop()
        
        self._proxyd = proxy( self._proxyAddress, self._proxyPort , self._urlOpener, proxyHandler=self.proxyHandler )
        self._proxyd.start2()

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'IP address where googleProxy will use to receive requests'
        o1 = option('proxyAddress', str(self._proxyAddress), d1, 'string')
        
        d2 = 'TCP port that the googleProxy server will use to receive requests'
        o2 = option('proxyPort', str(self._proxyPort), d2, 'integer')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        return ol

    def getExploitableVulns( self ):
        return []
        
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin exploits a service that google provides for mobile users and generates an HTTP proxy that can be
        used to navigate the web anonymously.
        
        Two configurable parameters exist:
            - proxyPort
            - proxyAddress
        '''
