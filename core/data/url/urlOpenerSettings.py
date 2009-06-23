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
from core.data.url.handlers.gzip_handler import HTTPGzipProcessor
from core.data.url.handlers.FastHTTPBasicAuthHandler import FastHTTPBasicAuthHandler
import core.data.url.handlers.logHandler as logHandler
import core.data.url.handlers.mangleHandler as mangleHandler
from core.data.url.handlers.urlParameterHandler import URLParameterHandler

from extlib.ntlm import ntlm
import core.data.url.handlers.HTTPNtlmAuthHandler

from core.controllers.configurable import configurable

# options
from core.data.options.option import option
from core.data.options.optionList import optionList


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
        self._urlParameterHandler = None
        self._ntlmAuthHandler = None
        # Keep alive handlers are created on buildOpeners()
        
        # Openers
        self._nonCacheOpener = None
        self._cacheOpener = None

        # Some internal variables
        self.needUpdate = True
        self.HeaderList = [('User-Agent','w3af.sourceforge.net')]        
        
        # By default, dont mangle any request/responses
        self._manglePlugins = []

        # User configured variables
        if cf.cf.getData('timeout') == None:
            # This is the first time we are executed...
        
            cf.cf.save('timeout', 10 )
            self._socket.setdefaulttimeout(cf.cf.getData('timeout'))
            cf.cf.save('headersFile', '' )
            cf.cf.save('cookieJarFile', '' )
            cf.cf.save('User-Agent', 'w3af.sourceforge.net' )
            
            cf.cf.save('proxyAddress', '' )
            cf.cf.save('proxyPort', 8080 )            
            
            cf.cf.save('basicAuthPass', '' )
            cf.cf.save('basicAuthUser', '' )
            cf.cf.save('basicAuthDomain', '' )

            cf.cf.save('ntlmAuthUser', '' )
            cf.cf.save('ntlmAuthPass', '' )
            
            cf.cf.save('ignoreSessCookies', False )
            cf.cf.save('maxFileSize', 400000 )
            cf.cf.save('maxRetrys', 2 )
            
            cf.cf.save('urlParameter', '' )
            
            # 404 settings
            cf.cf.save('404exceptions', []  )
            cf.cf.save('always404', [] )
            cf.cf.save('autodetect404', False )
            cf.cf.save('byDirectory404', False )
            cf.cf.save('byDirectoryAndExtension404', True)        
    
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
            cf.cf.save('headersFile', HeadersFile )
    
    def setHeadersList( self, hList ):
        '''
        @parameter hList: A list of tuples with (header,value) to be added to every request.
        @return: nothing
        '''
        for h, v in hList:
            self.HeaderList.append( (h,v) )
            om.out.debug( 'Added the following header: '+ h+ ': '+ v)
        
    def getHeadersFile( self ):
        return cf.cf.getData('headersFile')
        
    def setCookieJarFile(self, CookieJarFile ):
        om.out.debug( 'Called SetCookie')
        
        if CookieJarFile != '':
            cj = self._cookielib.MozillaCookieJar()
            try:
                cj.load( CookieJarFile )
            except Exception, e:
                raise w3afException( 'Error while loading cookiejar file. Description: ' + str(e) )
                
            self._cookieHandler = self._ulib.HTTPCookieProcessor(cj)
            cf.cf.save('cookieJarFile', CookieJarFile )
        
    def getCookieJarFile( self ):
        return cf.cf.getData('cookieJarFile')
    
    def setTimeout( self, timeout ):
        om.out.debug( 'Called SetTimeout(' + str(timeout)  + ')' )
        if timeout > 60 or timeout < 1:
            raise w3afException('The timeout parameter should be between 1 and 60 seconds.')
        else:
            cf.cf.save('timeout', timeout )
            
            # Set the default timeout
            # I dont need to use timeoutsocket.py , it has been added to python sockets
            self._socket.setdefaulttimeout(cf.cf.getData('timeout'))
        
    def getTimeout( self ):
        return cf.cf.getData('timeout')
        
    def setUserAgent( self, useragent ):
        om.out.debug( 'Called SetUserAgent')
        self.HeaderList = [ i for i in self.HeaderList if i[0]!='User-Agent']
        self.HeaderList.append( ('User-Agent',useragent) )
        cf.cf.save('User-Agent', useragent)
        
    def getUserAgent( self ):
        return cf.cf.getData('User-Agent')
        
    def setProxy( self, ip , port):
        om.out.debug( 'Called SetProxy(' + ip + ',' + str(port) + ')')
        if port > 65535 or port < 1:
            raise w3afException('Invalid port number: '+ str(port) )

        cf.cf.save('proxyAddress', ip )
        cf.cf.save('proxyPort', port )         
        
        # Remember that this line:
        #proxyMap = { 'http' : "http://" + ip + ":" + str(port) , 'https' : "https://" + ip + ":" + str(port) }
        # makes no sense, because urllib2.ProxyHandler doesn't support HTTPS proxies with CONNECT.
        # The proxying with CONNECT is implemented in keep-alive handler. (nasty!)
        proxyMap = { 'http' : "http://" + ip + ":" + str(port) }
        self._proxyHandler = self._ulib.ProxyHandler( proxyMap )

    def getProxy( self ):
        return cf.cf.getData('proxyAddress') + ':' + str(cf.cf.getData('proxyPort'))
        
    def setBasicAuth( self, url, username, password ):
        if url == '':
            raise w3afException('To properly configure the basic authentication settings, you should also set the auth domain. If you are unsure, you can set it to the target domain name.')
        
        cf.cf.save('basicAuthPass',  password)
        cf.cf.save('basicAuthUser', username )
        cf.cf.save('basicAuthDomain', url )            
        
        om.out.debug( 'Called SetBasicAuth')
        
        if not hasattr( self, '_password_mgr' ):
            # create a new password manager
            self._password_mgr = self._ulib.HTTPPasswordMgrWithDefaultRealm()

        # add the username and password
        if url.startswith('http://') or url.startswith('https://'):
            scheme, domain, path, x1, x2, x3 = self._uparse.urlparse( url )
            self._password_mgr.add_password(None, domain, username, password)
        else:
            domain = url
            scheme = 'http://'
            self._password_mgr.add_password(None, domain, username, password)

        self._basicAuthHandler = FastHTTPBasicAuthHandler(self._password_mgr)

        # Only for w3af, no usage in urllib2
        self._basicAuthStr = scheme + '://' + username + ':' + password + '@' + domain + '/'
        
        self.needUpdate = True

    def getBasicAuth( self ):
        scheme, domain, path, x1, x2, x3 = self._uparse.urlparse( cf.cf.getData('basicAuthDomain') )
        return scheme + '://' + cf.cf.getData('basicAuthUser') + ':' + cf.cf.getData('basicAuthPass') + '@' + domain + '/'
    
    def setNtlmAuth( self, url, username, password ):

        cf.cf.save('ntlmAuthPass',  password)
        cf.cf.save('ntlmAuthUser', username )
        
        om.out.debug( 'Called SetNtlmAuth')

        if not hasattr( self, '_password_mgr' ):
            # create a new password manager
            self._password_mgr = self._ulib.HTTPPasswordMgrWithDefaultRealm()

        # add the username and password
        if url.startswith('http://') or url.startswith('https://'):
            scheme, domain, path, x1, x2, x3 = self._uparse.urlparse( url )
            self._password_mgr.add_password(None, url, username, password)

        else:
            domain = url
            scheme = 'http://'
            self._password_mgr.add_password(None, url, username, password)

        self._ntlmAuthHandler = HTTPNtlmAuthHandler.HTTPNtlmAuthHandler(self._password_mgr)
   
        self.needUpdate = True
                        
    def buildOpeners(self):
        om.out.debug( 'Called buildOpeners')
        
        if self._cookieHandler == None and not cf.cf.getData('ignoreSessCookies'):
            cj = self._cookielib.MozillaCookieJar()
            self._cookieHandler = self._ulib.HTTPCookieProcessor(cj)
        
        # Instanciate the handlers passing the proxy as parameter
        self._kAHTTP = kAHTTP()
        self._kAHTTPS = kAHTTPS(self.getProxy())
        
        # Prepare the list of handlers
        handlers = []
        for handler in [ self._proxyHandler, self._basicAuthHandler,  \
                                self._ntlmAuthHandler, self._cookieHandler, \
                                MultipartPostHandler.MultipartPostHandler, \
                                self._kAHTTP, self._kAHTTPS, logHandler.logHandler, \
                                mangleHandler.mangleHandler( self._manglePlugins ), \
                                HTTPGzipProcessor, self._urlParameterHandler ]:
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

    def setManglePlugins( self, mp ):
        '''
        Configure the mangle plugins to be used.
        
        @parameter mp: A list of mangle plugin instances.
        '''
        self._manglePlugins = mp
        
    def getManglePlugins( self ):
        return self._manglePlugins
        
    def getMaxFileSize( self ):
        return cf.cf.getData('maxFileSize')
        
    def setMaxFileSize( self, fsize ):
        cf.cf.save('maxFileSize', fsize)
        
    def setMaxRetrys( self, retryN ):
        cf.cf.save('maxRetrys', retryN)
    
    def getMaxRetrys( self ):
        return cf.cf.getData('maxRetrys')
    
    def setUrlParameter ( self, urlParam ):
        # Do some input cleanup/validation
        urlParam = urlParam.replace("'", "")
        urlParam = urlParam.replace("\"", "")
        urlParam = urlParam.lstrip().rstrip()
        if urlParam != '':
            cf.cf.save('urlParameter', urlParam)
            self._urlParameterHandler = URLParameterHandler(urlParam)
    
    def getUrlParameter ( self ):
        return cf.cf.getData('urlParameter')

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''        
        d1 = 'The timeout for connections to the HTTP server'
        h1 = 'Set low timeouts for LAN use and high timeouts for slow Internet connections.'
        o1 = option('timeout', cf.cf.getData('timeout'), d1, 'integer', help=h1)
        
        d2 = 'Set the headers filename. This file has additional headers that are added to each request.'
        o2 = option('headersFile', cf.cf.getData('headersFile'), d2, 'string')

        d3 = 'Set the basic authentication username for HTTP requests'
        o3 = option('basicAuthUser', cf.cf.getData('basicAuthUser'), d3, 'string', tabid='Basic HTTP Authentication')

        d4 = 'Set the basic authentication password for HTTP requests'
        o4 = option('basicAuthPass', cf.cf.getData('basicAuthPass'), d4, 'string', tabid='Basic HTTP Authentication')

        d5 = 'Set the basic authentication domain for HTTP requests'
        h5 = 'This configures on which requests to send the authentication settings configured'
        h5 += ' in basicAuthPass and basicAuthUser. If you are unsure, just set it to the'
        h5 += ' target domain name.'
        o5 = option('basicAuthDomain', cf.cf.getData('basicAuthDomain'), d5, 'string', help=h5, tabid='Basic HTTP Authentication')

        d6= 'Set the NTLM authentication username for HTTP requests'
        o6 = option('ntlmAuthUser', cf.cf.getData('ntlmAuthUser'), d6, 'string', tabid='NTLM Authentication')

        d7 = 'Set the NTLM authentication password for HTTP requests'
        o7 = option('ntlmAuthPass', cf.cf.getData('ntlmAuthPass'), d7, 'string', tabid='NTLM Authentication')
                
        d8 = 'Set the cookiejar filename.'
        h8 = 'The cookiejar file must be in mozilla format'
        o8 = option('cookieJarFile', cf.cf.getData('cookieJarFile'), d8, 'string', help=h8, tabid='Cookies')

        d9 = 'Ignore session cookies'
        h9 = 'If set to True, w3af will ignore all session cookies sent by the web application.'
        o9 = option('ignoreSessCookies', cf.cf.getData('ignoreSessCookies'), d9, 'boolean', help=h9, tabid='Cookies')
       
        d10 = 'Proxy TCP port'
        h10 = 'TCP port for the remote proxy server to use. On windows systems, if you left this'
        h10 += ' setting blank w3af will use the system settings that are configured in Internet'
        h10 += ' Explorer.'
        o10 = option('proxyPort', cf.cf.getData('proxyPort'), d10, 'integer', help=h10, tabid='Outgoing proxy')

        d11 = 'Proxy IP address'
        h11 = 'IP address for the remote proxy server to use. On windows systems, if you left this'
        h11 += ' setting blank w3af will use the system settings that are configured in Internet'
        h11 += 'Explorer.'
        o11 = option('proxyAddress', cf.cf.getData('proxyAddress'), d11, 'string', help=d11, tabid='Outgoing proxy')

        d12 = 'User Agent header'
        h12 = 'User Agent header to send in request.'
        o12 = option('userAgent', cf.cf.getData('User-Agent'), d12, 'string', help=h12, tabid='Misc')

        d13 = 'Maximum file size'
        h13 = 'Indicates the maximum file size (in bytes) that w3af will GET/POST.'
        o13 = option('maxFileSize', cf.cf.getData('maxFileSize'), d13, 'integer', help=h13, tabid='Misc')

        d14 = 'Maximum number of retries'
        h14 = 'Indicates the maximum number of retries when requesting an URL.'
        o14 = option('maxRetrys', cf.cf.getData('maxRetrys'), d14, 'integer', help=h14, tabid='Misc')

        d15 = 'A comma separated list that determines what URLs will ALWAYS be detected as 404 pages.'
        o15 = option('always404', cf.cf.getData('always404'), d15, 'list', tabid='404 settings')

        d16 = 'A comma separated list that determines what URLs will NEVER be detected as 404 pages.'
        o16 = option('404exceptions', cf.cf.getData('404exceptions'), d16, 'list', tabid='404 settings')

        d17 = 'Perform 404 page autodetection.'
        o17 = option('autodetect404', cf.cf.getData('autodetect404'), d17, 'boolean', tabid='404 settings')

        d18 = 'Perform 404 page detection based on the knowledge found in the directory of the file'
        h18 = 'Only used when autoDetect404 is False.'
        o18 = option('byDirectory404', cf.cf.getData('byDirectory404'), d18, 'boolean', tabid='404 settings')

        d19 = 'Perform 404 page detection based on the knowledge found in the directory of the file'
        d19 += ' AND the file extension'
        h19 = 'Only used when autoDetect404 and byDirectory404 are False.'
        o19 = option('byDirectoryAndExtension404', cf.cf.getData('byDirectoryAndExtension404'), d19, 'boolean', tabid='404 settings')
        
        d20 = 'Append the given URL parameter to every accessed URL.'
        d20 += ' Example: http://www.foobar.com/index.jsp;<parameter>?id=2'
        o20 = option('urlParameter', cf.cf.getData('urlParameter'), d20, 'string')    

        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        ol.add(o5)
        ol.add(o6)
        ol.add(o7)
        ol.add(o8)
        ol.add(o9)
        ol.add(o10)
        ol.add(o11)
        ol.add(o12)
        ol.add(o13)
        ol.add(o14)
        ol.add(o15)
        ol.add(o16)
        ol.add(o17)
        ol.add(o18)
        ol.add(o19)
        ol.add(o20)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: An optionList object with the option objects for a plugin.
        @return: No value is returned.
        ''' 
        self.setTimeout( optionsMap['timeout'].getValue() )
        
        # Only apply changes if they exist
        if optionsMap['basicAuthDomain'].getValue() != cf.cf.getData('basicAuthDomain') or\
        optionsMap['basicAuthUser'].getValue() != cf.cf.getData('basicAuthUser') or\
        optionsMap['basicAuthPass'].getValue() != cf.cf.getData('basicAuthPass'):
            self.setBasicAuth( optionsMap['basicAuthDomain'].getValue(),
                                        optionsMap['basicAuthUser'].getValue(),
                                        optionsMap['basicAuthPass'].getValue()  )

        # Only apply changes if they exist
        if optionsMap['proxyAddress'].getValue() != cf.cf.getData('proxyAddress') or\
        optionsMap['proxyPort'].getValue() != cf.cf.getData('proxyPort'):
            self.setProxy( optionsMap['proxyAddress'].getValue(), optionsMap['proxyPort'].getValue() )
        
        self.setCookieJarFile( optionsMap['cookieJarFile'].getValue() )
        self.setHeadersFile( optionsMap['headersFile'].getValue() )        
        self.setUserAgent( optionsMap['userAgent'].getValue() )
        cf.cf.save('ignoreSessCookies', optionsMap['ignoreSessCookies'].getValue() )
        
        self.setMaxFileSize( optionsMap['maxFileSize'].getValue() )
        self.setMaxRetrys( optionsMap['maxRetrys'].getValue() )
        
        self.setUrlParameter( optionsMap['urlParameter'].getValue() )
        
        # 404 settings are saved here
        cf.cf.save('404exceptions', optionsMap['404exceptions'].getValue() )
        cf.cf.save('always404', optionsMap['always404'].getValue() )
        cf.cf.save('autodetect404', optionsMap['autodetect404'].getValue() )
        cf.cf.save('byDirectory404', optionsMap['byDirectory404'].getValue() )
        cf.cf.save('byDirectoryAndExtension404', optionsMap['byDirectoryAndExtension404'].getValue() )
        
    def getDesc( self ):
        return 'This section is used to configure URL settings that affect the core and all plugins.'
