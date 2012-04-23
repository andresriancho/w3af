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
from core.controllers.configurable import configurable
from core.controllers.w3afException import w3afException
from core.data.kb.config import cf as cfg
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.data.parsers.urlParser import url_object
from core.data.url.handlers.FastHTTPBasicAuthHandler import \
    FastHTTPBasicAuthHandler
from core.data.url.handlers.gzip_handler import HTTPGzipProcessor
from core.data.url.handlers.keepalive import HTTPHandler as kAHTTP, \
    HTTPSHandler as kAHTTPS
from core.data.url.handlers.logHandler import LogHandler
from core.data.url.handlers.redirect import HTTPErrorHandler, HTTP30XHandler
from core.data.url.handlers.urlParameterHandler import URLParameterHandler
import core.controllers.outputManager as om
import core.data.url.handlers.HTTPNtlmAuthHandler as HTTPNtlmAuthHandler
import core.data.url.handlers.MultipartPostHandler as MultipartPostHandler
import core.data.url.handlers.localCache as localCache
import core.data.url.handlers.mangleHandler as mangleHandler


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
        self._urlParameterHandler = None
        self._ntlmAuthHandler = None
        # Keep alive handlers are created on buildOpeners()
        
        # Openers
        self._nonCacheOpener = None
        self._cacheOpener = None

        # Some internal variables
        self.needUpdate = True
        
        #
        #   I've found some websites that check the user-agent string, and don't allow you to access
        #   if you don't have IE (mostly ASP.NET applications do this). So now we use the following
        #   user-agent string in w3af:
        user_agent = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0;'
        user_agent += ' w3af.sf.net)'
        #   which basically is the UA for IE8 running in Windows 7, plus our website :)
        self.HeaderList = [('User-Agent', user_agent)]
        
        # By default, dont mangle any request/responses
        self._manglePlugins = []

        # User configured variables
        if cfg.getData('timeout') is None:
            # This is the first time we are executed...
        
            cfg.save('timeout', 15 )
            self._socket.setdefaulttimeout(cfg.getData('timeout'))
            cfg.save('headersFile', '' )
            cfg.save('cookieJarFile', '' )
            cfg.save('User-Agent', 'w3af.sourceforge.net' )
            
            cfg.save('proxyAddress', '' )
            cfg.save('proxyPort', 8080 )            
            
            cfg.save('basicAuthPass', '' )
            cfg.save('basicAuthUser', '' )
            cfg.save('basicAuthDomain', '' )

            cfg.save('ntlmAuthDomain', '' )
            cfg.save('ntlmAuthUser', '' )
            cfg.save('ntlmAuthPass', '' )
            cfg.save('ntlmAuthURL', '' )
            
            cfg.save('ignoreSessCookies', False )
            cfg.save('maxFileSize', 400000 )
            cfg.save('maxRetrys', 2 )
            
            cfg.save('urlParameter', '' )
            
            # 404 settings
            cfg.save('never404', []  )
            cfg.save('always404', [] )
            cfg.save('404string', '' )
    
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
            cfg.save('headersFile', HeadersFile )
    
    def setHeadersList( self, hList ):
        '''
        @parameter hList: A list of tuples with (header,value) to be added to every request.
        @return: nothing
        '''
        for h, v in hList:
            self.HeaderList.append( (h,v) )
            om.out.debug( 'Added the following header: '+ h+ ': '+ v)
        
    def getHeadersFile( self ):
        return cfg.getData('headersFile')
        
    def setCookieJarFile(self, CookieJarFile ):
        om.out.debug( 'Called SetCookie')
        
        if CookieJarFile != '':
            cj = self._cookielib.MozillaCookieJar()
            try:
                cj.load( CookieJarFile )
            except Exception, e:
                raise w3afException( 'Error while loading cookiejar file. Description: ' + str(e) )
                
            self._cookieHandler = self._ulib.HTTPCookieProcessor(cj)
            cfg.save('cookieJarFile', CookieJarFile )
        
    def getCookieJarFile( self ):
        return cfg.getData('cookieJarFile')
    
    def setTimeout( self, timeout ):
        om.out.debug( 'Called SetTimeout(' + str(timeout)  + ')' )
        if timeout > 60 or timeout < 1:
            raise w3afException('The timeout parameter should be between 1 and 60 seconds.')
        else:
            cfg.save('timeout', timeout )
            
            # Set the default timeout
            # I dont need to use timeoutsocket.py , it has been added to python sockets
            self._socket.setdefaulttimeout(cfg.getData('timeout'))
        
    def getTimeout( self ):
        return cfg.getData('timeout')
        
    def setUserAgent( self, useragent ):
        om.out.debug( 'Called SetUserAgent')
        self.HeaderList = [ i for i in self.HeaderList if i[0]!='User-Agent']
        self.HeaderList.append( ('User-Agent',useragent) )
        cfg.save('User-Agent', useragent)
        
    def getUserAgent( self ):
        return cfg.getData('User-Agent')
        
    def setProxy( self, ip , port):
        '''
        Saves the proxy information and creates the handler.
        
        If the information is invalid it will set self._proxyHandler to None,
        so no proxy is used.
        
        @return: None
        '''
        om.out.debug( 'Called setProxy(%s,%s)' % (ip, port) )
        
        if not ip:
            #    The user doesn't want a proxy anymore
            cfg.save('proxyAddress', '' )
            cfg.save('proxyPort', '' )         
            self._proxyHandler = None
            return
            
        if port > 65535 or port < 1:
            #    The user entered something invalid
            self._proxyHandler = None
            raise w3afException('Invalid port number: '+ str(port) )

        #
        #    Great, we have all valid information.
        #
        cfg.save('proxyAddress', ip )
        cfg.save('proxyPort', port )         
        
        #
        #    Remember that this line:
        #
        #proxyMap = { 'http' : "http://" + ip + ":" + str(port) , 'https' : "https://" + ip + ":" + str(port) }
        #
        #    makes no sense, because urllib2.ProxyHandler doesn't support HTTPS proxies with CONNECT.
        #    The proxying with CONNECT is implemented in keep-alive handler. (nasty!)
        proxyMap = { 'http' : "http://" + ip + ":" + str(port) }
        self._proxyHandler = self._ulib.ProxyHandler( proxyMap )

    def getProxy( self ):
        return cfg.getData('proxyAddress') + ':' + str(cfg.getData('proxyPort'))
        
    def setBasicAuth(self, url, username, password):
        om.out.debug( 'Called SetBasicAuth')

        if not url:
            if url is None:
                raise w3afException(
                                'The entered basicAuthDomain URL is invalid!')
            elif username or password:
                msg = ('To properly configure the basic authentication '
                    'settings, you should also set the auth domain. If you '
                    'are unsure, you can set it to the target domain name.')
                raise w3afException(msg)
        else:
            if not hasattr(self, '_password_mgr'):
                # Create a new password manager
                self._password_mgr = self._ulib.HTTPPasswordMgrWithDefaultRealm()
    
            # Add the username and password
            domain = url.getDomain()
            protocol = url.getProtocol()
            protocol = protocol if protocol in ('http', 'https') else 'http'
            self._password_mgr.add_password(None, domain, username, password)
            self._basicAuthHandler = FastHTTPBasicAuthHandler(self._password_mgr)
    
            # Only for w3af, no usage in urllib2
            self._basicAuthStr = protocol + '://' + username + ':' + password + '@' + domain + '/'
            self.needUpdate = True
        
        # Save'em!
        cfg.save('basicAuthPass',  password)
        cfg.save('basicAuthUser', username )
        cfg.save('basicAuthDomain', url)

    def getBasicAuth( self ):
        scheme, domain, path, x1, x2, x3 = self._uparse.urlparse( cfg.getData('basicAuthDomain') )
        res = scheme + '://' + cfg.getData('basicAuthUser') + ':' 
        res += cfg.getData('basicAuthPass') + '@' + domain + '/'
        return res
    
    def setNtlmAuth( self, url, ntlm_domain, username, password ):

        cfg.save('ntlmAuthPass', password )
        cfg.save('ntlmAuthDomain', ntlm_domain )
        cfg.save('ntlmAuthUser', username )
        cfg.save('ntlmAuthURL', url )
        
        om.out.debug( 'Called SetNtlmAuth')

        if not hasattr( self, '_password_mgr' ):
            # create a new password manager
            self._password_mgr = self._ulib.HTTPPasswordMgrWithDefaultRealm()

        # HTTPNtmlAuthHandler expects username to have the domain name
        # separated with a '\', so that's what we do here:
        username = ntlm_domain + '\\' + username
        
        self._password_mgr.add_password(None, url, username, password)
        self._ntlmAuthHandler = HTTPNtlmAuthHandler.HTTPNtlmAuthHandler(self._password_mgr)
   
        self.needUpdate = True
                        
    def buildOpeners(self):
        om.out.debug('Called buildOpeners')
        
        if self._cookieHandler is None and not cfg.getData('ignoreSessCookies'):
            cj = self._cookielib.MozillaCookieJar()
            self._cookieHandler = self._ulib.HTTPCookieProcessor(cj)
        
        # Instantiate the handlers passing the proxy as parameter
        self._kAHTTP = kAHTTP()
        self._kAHTTPS = kAHTTPS(self.getProxy())
        self._cache_hdler = localCache.CacheHandler()
        
        # Prepare the list of handlers
        handlers = []
        for handler in [self._proxyHandler, self._basicAuthHandler,
                        self._ntlmAuthHandler, self._cookieHandler,
                        MultipartPostHandler.MultipartPostHandler,
                        self._kAHTTP, self._kAHTTPS, LogHandler,
                        HTTPErrorHandler, HTTP30XHandler,
                        mangleHandler.mangleHandler(self._manglePlugins),
                        HTTPGzipProcessor, self._urlParameterHandler, 
                        self._cache_hdler]:
            if handler:
                handlers.append(handler)
        
        self._nonCacheOpener = self._ulib.build_opener(*handlers)
        
        # Prevent the urllib from putting his user-agent header
        self._nonCacheOpener.addheaders = [ ('Accept', '*/*') ]
        
    def getCustomUrlopen(self):
        return self._nonCacheOpener

    def setManglePlugins( self, mp ):
        '''
        Configure the mangle plugins to be used.
        
        @parameter mp: A list of mangle plugin instances.
        '''
        self._manglePlugins = mp
        
    def getManglePlugins( self ):
        return self._manglePlugins
        
    def getMaxFileSize( self ):
        return cfg.getData('maxFileSize')
        
    def setMaxFileSize( self, fsize ):
        cfg.save('maxFileSize', fsize)
        
    def setMaxRetrys( self, retryN ):
        cfg.save('maxRetrys', retryN)
    
    def getMaxRetrys( self ):
        return cfg.getData('maxRetrys')
    
    def setUrlParameter ( self, urlParam ):
        # Do some input cleanup/validation
        urlParam = urlParam.replace("'", "")
        urlParam = urlParam.replace("\"", "")
        urlParam = urlParam.lstrip().rstrip()
        if urlParam != '':
            cfg.save('urlParameter', urlParam)
            self._urlParameterHandler = URLParameterHandler(urlParam)
    
    def getUrlParameter ( self ):
        return cfg.getData('urlParameter')

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''        
        d1 = 'The timeout for connections to the HTTP server'
        h1 = 'Set low timeouts for LAN use and high timeouts for slow Internet connections.'
        o1 = option('timeout', cfg.getData('timeout'), d1, 'integer', help=h1)
        
        d2 = 'Set the headers filename. This file has additional headers that are added to each request.'
        o2 = option('headersFile', cfg.getData('headersFile'), d2, 'string')

        d3 = 'Set the basic authentication username for HTTP requests'
        o3 = option('basicAuthUser', cfg.getData('basicAuthUser'), d3, 'string', tabid='Basic HTTP Authentication')

        d4 = 'Set the basic authentication password for HTTP requests'
        o4 = option('basicAuthPass', cfg.getData('basicAuthPass'), d4, 'string', tabid='Basic HTTP Authentication')

        d5 = 'Set the basic authentication domain for HTTP requests'
        h5 = 'This configures on which requests to send the authentication settings configured'
        h5 += ' in basicAuthPass and basicAuthUser. If you are unsure, just set it to the'
        h5 += ' target domain name.'
        o5 = option('basicAuthDomain', cfg.getData('basicAuthDomain'), d5, 'string', help=h5, tabid='Basic HTTP Authentication')

        
        d6a= 'Set the NTLM authentication domain (the windows domain name) for HTTP requests'
        o6a = option('ntlmAuthDomain', cfg.getData('ntlmAuthDomain'), d6a, 'string', tabid='NTLM Authentication')
        
        d6= 'Set the NTLM authentication username for HTTP requests'
        o6 = option('ntlmAuthUser', cfg.getData('ntlmAuthUser'), d6, 'string', tabid='NTLM Authentication')

        d7 = 'Set the NTLM authentication password for HTTP requests'
        o7 = option('ntlmAuthPass', cfg.getData('ntlmAuthPass'), d7, 'string', tabid='NTLM Authentication')

        d7b = 'Set the NTLM authentication domain for HTTP requests'
        h7b = 'This configures on which requests to send the authentication settings configured'
        h7b += ' in ntlmAuthPass and ntlmAuthUser. If you are unsure, just set it to the'
        h7b += ' target domain name.'
        o7b = option('ntlmAuthURL', cfg.getData('ntlmAuthURL'), d7b, 'string', tabid='NTLM Authentication')
                
        d8 = 'Set the cookiejar filename.'
        h8 = 'The cookiejar file MUST be in mozilla format.'
        h8 += ' An example of a valid mozilla cookie jar file follows:\n\n'
        h8 += '# Netscape HTTP Cookie File\n'
        h8 += '.domain.com    TRUE   /       FALSE   1731510001      user    admin\n\n'
        h8 += 'The comment IS mandatory. Take special attention to spaces.'
        o8 = option('cookieJarFile', cfg.getData('cookieJarFile'), d8, 'string', help=h8, tabid='Cookies')

        d9 = 'Ignore session cookies'
        h9 = 'If set to True, w3af will ignore all session cookies sent by the web application.'
        o9 = option('ignoreSessCookies', cfg.getData('ignoreSessCookies'), d9, 'boolean', help=h9, tabid='Cookies')
       
        d10 = 'Proxy TCP port'
        h10 = 'TCP port for the remote proxy server to use. On Microsoft Windows systems, w3af'
        h10 += ' will use the proxy settings that are configured in Internet Explorer.'
        o10 = option('proxyPort', cfg.getData('proxyPort'), d10, 'integer', help=h10, tabid='Outgoing proxy')

        d11 = 'Proxy IP address'
        h11 = 'IP address for the remote proxy server to use. On Microsoft Windows systems, w3af'
        h11 += ' will use the proxy settings that are configured in Internet Explorer.'
        o11 = option('proxyAddress', cfg.getData('proxyAddress'), d11, 'string', help=h11, tabid='Outgoing proxy')

        d12 = 'User Agent header'
        h12 = 'User Agent header to send in request.'
        o12 = option('userAgent', cfg.getData('User-Agent'), d12, 'string', help=h12, tabid='Misc')

        d13 = 'Maximum file size'
        h13 = 'Indicates the maximum file size (in bytes) that w3af will GET/POST.'
        o13 = option('maxFileSize', cfg.getData('maxFileSize'), d13, 'integer', help=h13, tabid='Misc')

        d14 = 'Maximum number of retries'
        h14 = 'Indicates the maximum number of retries when requesting an URL.'
        o14 = option('maxRetrys', cfg.getData('maxRetrys'), d14, 'integer', help=h14, tabid='Misc')

        d15 = 'A comma separated list that determines what URLs will ALWAYS be detected as 404 pages.'
        o15 = option('always404', cfg.getData('always404'), d15, 'list', tabid='404 settings')

        d16 = 'A comma separated list that determines what URLs will NEVER be detected as 404 pages.'
        o16 = option('never404', cfg.getData('never404'), d16, 'list', tabid='404 settings')

        d17 = 'If this string is found in an HTTP response, then it will be tagged as a 404.'
        o17 = option('404string', cfg.getData('404string'), d17, 'string', tabid='404 settings')

        d18 = 'Append the given URL parameter to every accessed URL.'
        d18 += ' Example: http://www.foobar.com/index.jsp;<parameter>?id=2'
        o18 = option('urlParameter', cfg.getData('urlParameter'), d18, 'string')    

        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        ol.add(o5)
        ol.add(o6a)
        ol.add(o6)
        ol.add(o7)
        ol.add(o7b)
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
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: An optionList object with the option objects for a plugin.
        @return: No value is returned.
        '''
        getOptsMapValue = lambda n: optionsMap[n].getValue()
        self.setTimeout(getOptsMapValue('timeout'))
        
        # Only apply changes if they exist
        bAuthDomain = getOptsMapValue('basicAuthDomain')
        bAuthUser = getOptsMapValue('basicAuthUser')
        bAuthPass = getOptsMapValue('basicAuthPass')
        
        if bAuthDomain != cfg['basicAuthDomain'] or \
            bAuthUser != cfg['basicAuthUser'] or \
            bAuthPass != cfg['basicAuthPass']:
            try:
                bAuthDomain = url_object(bAuthDomain) if bAuthDomain else ''
            except ValueError:
                bAuthDomain = None
            
            self.setBasicAuth(bAuthDomain, bAuthUser, bAuthPass)
        
        ntlmAuthDomain = getOptsMapValue('ntlmAuthDomain')
        ntlmAuthUser = getOptsMapValue('ntlmAuthUser')
        ntlmAuthPass = getOptsMapValue('ntlmAuthPass')
        ntlmAuthURL = getOptsMapValue('ntlmAuthURL')
        
        if ntlmAuthDomain != cfg['ntlmAuthDomain'] or \
           ntlmAuthUser != cfg['ntlmAuthUser'] or \
           ntlmAuthPass != cfg['ntlmAuthPass'] or \
           ntlmAuthURL!= cfg['ntlmAuthURL']:
            self.setNtlmAuth(ntlmAuthURL, ntlmAuthDomain, ntlmAuthUser, ntlmAuthPass)

        # Only apply changes if they exist
        proxyAddress = getOptsMapValue('proxyAddress')
        proxyPort = getOptsMapValue('proxyPort')
        
        if proxyAddress != cfg['proxyAddress'] or \
            proxyPort != cfg['proxyPort']:
            self.setProxy(proxyAddress, proxyPort)
        
        self.setCookieJarFile(getOptsMapValue('cookieJarFile'))
        self.setHeadersFile(getOptsMapValue('headersFile') )        
        self.setUserAgent(getOptsMapValue('userAgent'))
        cfg['ignoreSessCookies'] = getOptsMapValue('ignoreSessCookies')
        
        self.setMaxFileSize(getOptsMapValue('maxFileSize'))
        self.setMaxRetrys(getOptsMapValue('maxRetrys'))
        
        self.setUrlParameter(getOptsMapValue('urlParameter'))
        
        # 404 settings are saved here
        cfg['never404'] = getOptsMapValue('never404')
        cfg['always404'] = getOptsMapValue('always404')
        cfg['404string'] = getOptsMapValue('404string')
        
    def getDesc( self ):
        return ('This section is used to configure URL settings that '
            'affect the core and all plugins.')
    