'''
urlOpenerSettings.py

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

# Some misc imports
import core.controllers.outputManager as om
import core.data.kb.config as cf
from core.controllers.w3afException import w3afException

# Handler imports
import core.data.url.handlers.localCache as localCache
from core.data.url.handlers.keepalive import HTTPHandler as kAHTTP
from core.data.url.handlers.keepalive import HTTPSHandler as kAHTTPS
import core.data.url.handlers.MultipartPostHandler as MultipartPostHandler
import core.data.url.handlers.certHTTPSHandler as certHTTPSHandler
import core.data.url.handlers.logHandler as logHandler
import core.data.url.handlers.idHandler as idHandler
import core.data.url.handlers.mangleHandler as mangleHandler

from core.controllers.configurable import configurable
from core.controllers.misc.parseOptions import parseOptions

class urlOpenerSettings( configurable ):
    '''
    This is a urllib2 configuration manager.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    import urllib2 as _ulib
    import socket as _socket
    import urlparse as _uparse
    from time import sleep as _sleep
    from random import random as _random
    from robotparser import RobotFileParser as _rparser
    import cookielib as _cookielib
    
    def __init__(self):
        
        # Set the openers to None
        self._basicAuthHandler = None
        self._proxyHandler = None
        self._cookieHandler = None
        self._httpsHandler = None
        self._mangleHandler = None
        self._cookieHandler = None
        
        #self._keepAliveHandler = None
        self._kAHTTP = kAHTTP()
        self._kAHTTPS = kAHTTPS()
        
        # Openers
        self._nonCacheOpener = None
        self._cacheOpener = None
        
        # User configured variables
        self._timeout = 10
        self._socket.setdefaulttimeout(self._timeout)
        self._headersFile = ''
        self._cookieJarFile = ''
        self._userAgent = 'w3af.sourceforge.net'
        cf.cf.save('User-Agent', self._userAgent)
        
        self._proxyAddress = ''
        self._proxyPort = 8080
        
        self._basicAuthPass = ''
        self._basicAuthUser = ''
        self._basicAuthDomain = ''
        
        self.HeaderList = [('User-Agent',self._userAgent)]
        
        self._sslCertFile = ''
        self._sslKeyFile = ''
        
        self._ignoreSessCookies = False
        self._maxFileSize = 400000
        self._maxRetrys = 2
        
        self.needUpdate = True
        
        # By default, dont mangle any request/responses
        self._manglePlugins = []
    
    def setHeadersFile(self, HeadersFile ):
        '''
        Sets the special headers to use, this headers are specified in a file by the user.
        The file can have multiple lines, each line should have the following structure :
            - HEADER:VALUE_OF_HEADER
        
        @parameter HeadersFile: The filename where the special headers are specified.
        @return: No value is returned.
        '''
        om.out.debug( 'Called SetHeaders')
        if HeadersFile != '':
            try:
                f=open(HeadersFile, 'r')
            except:
                raise w3afException('Unable to open headers file: ' + HeadersFile )
            
            hList = []
            for line in f:
                HeaderName = line.split(':')[0]
                HeaderValue = ':'.join( line.split(':')[1:] )
                HeaderValue = HeaderValue.strip()
                hList.append( (HeaderName,HeaderValue) )
            
            self.setHeadersList( hList )
            self._headersFile = HeadersFile
    
    def setHeadersList( self, hList ):
        '''
        @parameter hList: A list of tuples with (header,value) to be added to every request.
        @return: nothing
        '''
        for h, v in hList:
            self.HeaderList.append( (h,v) )
            om.out.debug( 'Added the following header: '+ h+ ': '+ v)
        
    
    def getHeadersFile( self ):
        return self._headersFile
        
    def setCookieJarFile(self, CookieJarFile ):
        om.out.debug( 'Called SetCookie')
        
        if CookieJarFile != '':
            cj = self._cookielib.MozillaCookieJar()
            try:
                cj.load( CookieJarFile )
            except Exception, e:
                raise w3afException( 'Error while loading cookiejar file. Description: ' + str(e) )
                
            self._cookieHandler = self._ulib.HTTPCookieProcessor(cj)
            self._cookieJarFile = CookieJarFile
        
    def getCookieJarFile( self ):
        return self._cookieJarFile
    
    def getSSLKeyFile( self ):
        '''
        @return: A string with the SSL key path and filename.
        '''
        return self._sslKeyFile
        
    def setSSLKeyFile( self, keyFile ):
        '''
        @parameter keyFile: A string with the SSL key path and filename.
        @return: None
        ''' 
        self._sslKeyFile = keyFile
        
    def getSSLCertFile( self ):
        '''
        @return: A string with the SSL cert path and filename.
        '''
        return self._sslCertFile
        
    def setSSLCertFile( self, file ):
        '''
        @parameter file: A string with the SSL cert path and filename.
        @return: None
        '''     
        self._sslCertFile = file
    
    def setTimeout( self, timeout ):
        om.out.debug( 'Called SetTimeout(' + str(timeout)  + ')' )
        if timeout > 60 or timeout < 1:
            raise w3afException('The timeout parameter should be between 1 and 60 seconds.')
        else:
            self._timeout = timeout
            
            # Set the default timeout
            # I dont need to use timeoutsocket.py , it has been added to python sockets
            self._socket.setdefaulttimeout(self._timeout)
        
    def getTimeout( self ):
        return self._timeout
        
    def setUserAgent( self, useragent ):
        om.out.debug( 'Called SetUserAgent')
        self.HeaderList = [ i for i in self.HeaderList if i[0]!='User-Agent']
        self.HeaderList.append( ('User-Agent',useragent) )
        self._userAgent = useragent
        cf.cf.save('User-Agent', useragent)
        
    def getUserAgent( self ):
        return self._userAgent
        
    def setProxy( self, ip , port):
        om.out.debug( 'Called SetProxy(' + ip + ',' + str(port) + ')')
        if port > 65535 or port < 1:
            raise w3afException('Invalid port number.')

        self._proxyPort = port
        self._proxyAddress = ip
        
        proxyMap = { 'http' : "http://" + ip + ":" + str(port) , 'https' : "https://" + ip + ":" + str(port) }
        self._proxyHandler = self._ulib.ProxyHandler( proxyMap )
        self._proxy = ip + ":" + str(port) 

    def getProxy( self ):
        return self._proxy
        
    def setBasicAuth( self, url, username, password ):
        self._basicAuthDomain = url
        self._basicAuthUser = username
        self._basicAuthPass = password
        
        om.out.debug( 'Called SetBasicAuth')
        
        if not hasattr( self, '_password_mgr' ):
            # create a password manager
            self._password_mgr = self._ulib.HTTPPasswordMgrWithDefaultRealm()

        # add the username and password
        scheme, domain, path, x1, x2, x3 = self._uparse.urlparse( url )
        self._password_mgr.add_password(None, domain, username, password)

        self._basicAuthHandler = self._ulib.HTTPBasicAuthHandler(self._password_mgr)
        
        # Only for w3af, no usage in urllib2
        self._basicAuthStr = scheme + '://' + username + ':' + password + '@' + domain + '/'
        
        self.needUpdate = True
    
    def getBasicAuth( self ):
        return self._basicAuthStr
        
    def buildOpeners(self):
        om.out.debug( 'Called buildOpeners')
        
        if self._cookieHandler == None and not self._ignoreSessCookies:
            cj = self._cookielib.MozillaCookieJar()
            self._cookieHandler = self._ulib.HTTPCookieProcessor(cj)
        
        # Prepare the list of handlers
        handlers = []
        for handler in [ self._proxyHandler, self._basicAuthHandler,  \
                                self._cookieHandler, \
                                MultipartPostHandler.MultipartPostHandler, \
                                self._kAHTTP, self._kAHTTPS, logHandler.logHandler, \
                                idHandler.idHandler, mangleHandler.mangleHandler( self._manglePlugins ) ]:
            if handler:
                handlers.append(handler)
        
        self._nonCacheOpener = apply( self._ulib.build_opener, tuple(handlers) )
        
        # Prevent the urllib from putting his user-agent header
        self._nonCacheOpener.addheaders = [ ('Accept', '*/*') ]
        
        # Add the local cache to the list of handlers
        handlers.append( localCache.CacheHandler() )
        self._cacheOpener = apply( self._ulib.build_opener, tuple(handlers) )
        
        # Prevent the urllib from putting his user-agent header
        self._cacheOpener.addheaders = [ ('Accept', '*/*') ]
        
        # Use this if you want to "bypass" the cache opener
        # debugging purposes only
        #self._cacheOpener = self._nonCacheOpener
        
    def getCustomUrlopen(self):
        return self._nonCacheOpener
        
    def getCachedUrlopen(self):
        return self._cacheOpener
    
    def getCfg( self ):
        '''
        This is a faster and simpler way to call all getters.
        '''
        result = {}
        
        result['timeout'] = self.getTimeout()
        result['basicAuth'] = self.getBasicAuth()
        result['cookie'] = self.getCookie()
        result['headers'] = self.getHeadersFile()
        result['proxy'] = self.getProxy()
        result['userAgent'] = self.getUserAgent()
        result['ignoreSessionCookies'] = self.ignoreSessionCookies
        
        return result
        
    def setManglePlugins( self, mp ):
        '''
        Configure the mangle plugins to be used.
        
        @parameter mp: A list of mangle plugin instances.
        '''
        self._manglePlugins = mp
        
    def getManglePlugins( self ):
        return self._manglePlugins
        
    def getMaxFileSize( self ):
        return self._maxFileSize
        
    def setMaxFileSize( self, fsize ):
        self._maxFileSize = 400000
        
    def setMaxRetrys( self, retryN ):
        self._maxRetrys = retryN
    
    def getMaxRetrys( self ):
        return self._maxRetrys
    
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
            <Option name="timeout">\
                <default>'+str(self._timeout)+'</default>\
                <desc>The timeout for connections to the HTTP server</desc>\
                <help>Set low timeouts for LAN use and high timeouts for slow Internet connections.</help>\
                <type>integer</type>\
            </Option>\
            <Option name="headersFile">\
                <default>'+str(self._headersFile)+'</default>\
                <desc>Set the headers filename. This file has additional headers that are added to each request.</desc>\
                <type>string</type>\
            </Option>\
            <Option name="basicAuthUser">\
                <default>'+str(self._basicAuthUser)+'</default>\
                <desc>Set the basic authentication username for HTTP requests</desc>\
                <tabID>Basic Authentication</tabID>\
                <type>string</type>\
                <tabid>Authentication</tabid>\
                </Option>\
            <Option name="basicAuthPass">\
                <default>'+str(self._basicAuthPass)+'</default>\
                <desc>Set the basic authentication password for HTTP requests</desc>\
                <tabID>Basic Authentication</tabID>\
                <tabid>Authentication</tabid>\
                <type>string</type>\
            </Option>\
            <Option name="basicAuthDomain">\
                <default>'+str(self._basicAuthDomain)+'</default>\
                <desc>Set the basic authentication domain for HTTP requests</desc>\
                <help>This configures on which request to send the authentication settings configured in basicAuthPass and basicAuthUser.</help>\
                <tabID>Basic Authentication</tabID>\
                <tabid>Authentication</tabid>\
                <type>string</type>\
            </Option>\
            <Option name="cookieJarFile">\
                <default>'+str(self._cookieJarFile)+'</default>\
                <desc>Set the cookiejar filename.</desc>\
                <help>The cookiejar file must be in mozilla format</help>\
                <tabid>Cookies</tabid>\
                <type>string</type>\
            </Option>\
            <Option name="ignoreSessCookies">\
                <default>'+str(self._ignoreSessCookies)+'</default>\
                <desc>Ignore session cookies</desc>\
                <help>If set to True, w3af will ignore all session cookies sent by the web application.</help>\
                <tabid>Cookies</tabid>\
                <type>boolean</type>\
            </Option>\
            <Option name="proxyPort">\
                <default>'+str(self._proxyPort)+'</default>\
                <desc>Proxy TCP port</desc>\
                <help>TCP port for the remote proxy server to use.</help>\
                <tabid>Proxy</tabid>\
                <type>integer</type>\
            </Option>\
            <Option name="proxyAddress">\
                <default>'+str(self._proxyAddress)+'</default>\
                <desc>Proxy IP address</desc>\
                <help>IP address for the remote proxy server to use.</help>\
                <tabid>Proxy</tabid>\
                <type>string</type>\
            </Option>\
            <Option name="userAgent">\
                <default>'+str(self._userAgent)+'</default>\
                <desc>User Agent header</desc>\
                <help>User Agent header to send in request.</help>\
                <type>string</type>\
            </Option>\
            <Option name="maxFileSize">\
                <default>'+str(self._maxFileSize)+'</default>\
                <desc>Indicates the maximum file size (in bytes) that w3af will GET/POST.</desc>\
                <type>integer</type>\
            </Option>\
            <Option name="maxRetrys">\
                <default>'+str(self._maxRetrys)+'</default>\
                <desc>Indicates the maximum number of retries when requesting an URL.</desc>\
                <type>integer</type>\
            </Option>\
        </OptionList>\
        '
        
    def setOptions( self, OptionMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter OptionMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        f00, OptionMap = parseOptions( 'url-settings', OptionMap )
        if OptionMap['timeout'] != self._timeout:
            self.setTimeout( OptionMap['timeout'] )
            
        if OptionMap['headersFile'] != self._headersFile:
            self.setHeadersFile( OptionMap['headersFile'] )
            
        if OptionMap['basicAuthDomain'] != self._basicAuthDomain or \
        OptionMap['basicAuthUser'] != self._basicAuthUser or \
        OptionMap['basicAuthPass'] != self._basicAuthPass:
            self.setBasicAuth( OptionMap['basicAuthDomain'], OptionMap['basicAuthUser'], OptionMap['basicAuthPass']  )
        
        if OptionMap['cookieJarFile'] != self._cookieJarFile:
            self.setCookieJarFile( OptionMap['cookieJarFile'] )
            
        if OptionMap['proxyAddress'] != self._proxyAddress or OptionMap['proxyPort'] != self._proxyPort:
            self.setProxy( OptionMap['proxyAddress'], OptionMap['proxyPort'] )
            
        self.setUserAgent( OptionMap['userAgent'] )
        self.setMaxFileSize( OptionMap['maxFileSize'] )
        self._ignoreSessCookies = OptionMap['ignoreSessCookies']
        self.setMaxRetrys( OptionMap['maxRetrys'] )
        
    def getDesc( self ):
        return 'This section is used to configure URL settings that affect the core and all plugins.'
