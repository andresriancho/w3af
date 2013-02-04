'''
opener_settings.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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
import urllib2
import socket
import urlparse
import cookielib

import core.controllers.output_manager as om
import core.data.url.handlers.ntlm_auth as HTTPNtlmAuthHandler
import core.data.url.handlers.MultipartPostHandler as MultipartPostHandler
import core.data.url.handlers.mangleHandler as mangleHandler

from core.controllers.configurable import Configurable
from core.controllers.exceptions import w3afException
from core.data.kb.config import cf as cfg
from core.data.options.opt_factory import opt_factory
from core.data.options.option_list import OptionList
from core.data.parsers.url import URL
from core.data.url.handlers.fast_basic_auth import FastHTTPBasicAuthHandler
from core.data.url.handlers.cookie_handler import CookieHandler
from core.data.url.handlers.gzip_handler import HTTPGzipProcessor
from core.data.url.handlers.keepalive import HTTPHandler as kAHTTP
from core.data.url.handlers.keepalive import HTTPSHandler as kAHTTPS
from core.data.url.handlers.logHandler import LogHandler
from core.data.url.handlers.redirect import HTTPErrorHandler, HTTP30XHandler
from core.data.url.handlers.urlParameterHandler import URLParameterHandler
from core.data.url.handlers.cache import CacheHandler


class OpenerSettings(Configurable):
    '''
    This is a urllib2 configuration manager.

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    def __init__(self):

        # Set the openers to None
        self._basicAuthHandler = None
        self._proxy_handler = None
        self._kAHTTP = None
        self._kAHTTPS = None
        self._mangleHandler = None
        self._url_parameterHandler = None
        self._ntlmAuthHandler = None
        self._cache_hdler = None
        # Keep alive handlers are created on build_openers()

        cj = cookielib.MozillaCookieJar()
        self._cookieHandler = CookieHandler(cj)

        # Openers
        self._uri_opener = None

        # Some internal variables
        self.need_update = True

        #
        #    I've found some websites that check the user-agent string, and
        #    don't allow you to access if you don't have IE (mostly ASP.NET
        #    applications do this). So now we use the following user-agent
        #    string in w3af:
        #
        user_agent = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0;'
        user_agent += ' w3af.org)'
        #   which basically is the UA for IE8 running in Windows 7, plus our website :)
        self.header_list = [('User-Agent', user_agent)]

        # By default, dont mangle any request/responses
        self._mangle_plugins = []

        # User configured variables
        if cfg.get('timeout') is None:
            # This is the first time we are executed...

            cfg.save('timeout', 15)
            socket.setdefaulttimeout(cfg.get('timeout'))
            cfg.save('headers_file', '')
            cfg.save('cookie_jar_file', '')
            cfg.save('user_agent', 'w3af.org')

            cfg.save('proxy_address', '')
            cfg.save('proxy_port', 8080)

            cfg.save('basic_auth_passwd', '')
            cfg.save('basic_auth_user', '')
            cfg.save('basic_auth_domain', '')

            cfg.save('ntlm_auth_domain', '')
            cfg.save('ntlm_auth_user', '')
            cfg.save('ntlm_auth_passwd', '')
            cfg.save('ntlm_auth_url', '')

            cfg.save('ignore_session_cookies', False)
            cfg.save('max_file_size', 400000)
            cfg.save('max_http_retries', 2)

            cfg.save('url_parameter', '')

            # 404 settings
            cfg.save('never_404', [])
            cfg.save('always_404', [])
            cfg.save('string_match_404', '')

    def set_headers_file(self, headers_file):
        '''
        Sets the special headers to use, this headers are specified in a file by the user.
        The file can have multiple lines, each line should have the following structure :
            - HEADER:VALUE_OF_HEADER

        @param headers_file: The filename where the special headers are specified.
        @return: No value is returned.
        '''
        om.out.debug('Called SetHeaders()')
        if headers_file != '':
            try:
                f = open(headers_file, 'r')
            except:
                raise w3afException(
                    'Unable to open headers file: ' + headers_file)

            header_list = []
            for line in f:
                header_name = line.split(':')[0]
                header_value = ':'.join(line.split(':')[1:])
                header_value = header_value.strip()
                header_list.append((header_name, header_value))

            self.set_header_list(header_list)
            cfg.save('headers_file', headers_file)

    def set_header_list(self, header_list):
        '''
        @param header_list: A list of tuples with (header,value) to be added
                            to every request.
        @return: nothing
        '''
        for h, v in header_list:
            self.header_list.append((h, v))
            om.out.debug('Added the following header: %s:%s' % (h,v))

    def close_connections(self):
        handlers = (self._kAHTTP, self._kAHTTPS)
        for handler in handlers:
            if handler is not None:
                handler.close_all()

    def get_headers_file(self):
        return cfg.get('headers_file')

    def set_cookie_jar_file(self, CookieJarFile):
        om.out.debug('Called SetCookie')

        if CookieJarFile != '':
            cj = cookielib.MozillaCookieJar()
            try:
                cj.load(CookieJarFile)
            except Exception, e:
                raise w3afException('Error while loading cookiejar file. Description: ' + str(e))

            self._cookieHandler = CookieHandler(cj)
            cfg.save('cookie_jar_file', CookieJarFile)

    def get_cookie_jar_file(self):
        return cfg.get('cookie_jar_file')

    def get_cookies(self):
        '''
        @return: The cookies that were collected during this scan.
        '''
        return self._cookieHandler.cookiejar
    
    def clear_cookies(self):
        self._cookieHandler.cookiejar.clear()
        self._cookieHandler.cookiejar.clear_session_cookies()

    def set_timeout(self, timeout):
        om.out.debug('Called SetTimeout(' + str(timeout) + ')')
        if timeout > 60 or timeout < 1:
            raise w3afException(
                'The timeout parameter should be between 1 and 60 seconds.')
        else:
            cfg.save('timeout', timeout)

            # Set the default timeout
            # I dont need to use timeoutsocket.py , it has been added to python sockets
            socket.setdefaulttimeout(cfg.get('timeout'))

    def get_timeout(self):
        return cfg.get('timeout')

    def set_user_agent(self, user_agent):
        om.out.debug('Called set_user_agent')
        self.header_list = [i for i in self.header_list if i[0]
                            != 'user_agent']
        self.header_list.append(('User-Agent', user_agent))
        cfg.save('user_agent', user_agent)

    def get_user_agent(self):
        return cfg.get('user_agent')

    def set_proxy(self, ip, port):
        '''
        Saves the proxy information and creates the handler.

        If the information is invalid it will set self._proxy_handler to None,
        so no proxy is used.

        @return: None
        '''
        om.out.debug('Called set_proxy(%s,%s)' % (ip, port))

        if not ip:
            #    The user doesn't want a proxy anymore
            cfg.save('proxy_address', '')
            cfg.save('proxy_port', '')
            self._proxy_handler = None
            return

        if port > 65535 or port < 1:
            #    The user entered something invalid
            self._proxy_handler = None
            raise w3afException('Invalid port number: ' + str(port))

        #
        #    Great, we have all valid information.
        #
        cfg.save('proxy_address', ip)
        cfg.save('proxy_port', port)

        #
        #    Remember that this line:
        #
        #proxyMap = { 'http' : "http://" + ip + ":" + str(port) , 'https' : "https://" + ip + ":" + str(port) }
        #
        #    makes no sense, because urllib2.ProxyHandler doesn't support HTTPS proxies with CONNECT.
        #    The proxying with CONNECT is implemented in keep-alive handler. (nasty!)
        proxyMap = {'http': "http://" + ip + ":" + str(port)}
        self._proxy_handler = urllib2.ProxyHandler(proxyMap)

    def get_proxy(self):
        return cfg.get('proxy_address') + ':' + str(cfg.get('proxy_port'))

    def set_basic_auth(self, url, username, password):
        om.out.debug('Called SetBasicAuth')

        if not url:
            if url is None:
                raise w3afException(
                    'The entered basic_auth_domain URL is invalid!')
            elif username or password:
                msg = ('To properly configure the basic authentication '
                       'settings, you should also set the auth domain. If you '
                       'are unsure, you can set it to the target domain name.')
                raise w3afException(msg)
        else:
            if not hasattr(self, '_password_mgr'):
                # Create a new password manager
                self._password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

            # Add the username and password
            domain = url.get_domain()
            protocol = url.get_protocol()
            protocol = protocol if protocol in ('http', 'https') else 'http'
            self._password_mgr.add_password(None, domain, username, password)
            self._basicAuthHandler = FastHTTPBasicAuthHandler(
                self._password_mgr)

            # Only for w3af, no usage in urllib2
            self._basicAuthStr = protocol + '://' + username + \
                ':' + password + '@' + domain + '/'
            self.need_update = True

        # Save'em!
        cfg.save('basic_auth_passwd', password)
        cfg.save('basic_auth_user', username)
        cfg.save('basic_auth_domain', url)

    def get_basic_auth(self):
        scheme, domain, path, x1, x2, x3 = urlparse.urlparse(
            cfg.get('basic_auth_domain'))
        res = scheme + '://' + cfg.get('basic_auth_user') + ':'
        res += cfg.get('basic_auth_passwd') + '@' + domain + '/'
        return res

    def set_ntlm_auth(self, url, ntlm_domain, username, password):

        cfg.save('ntlm_auth_passwd', password)
        cfg.save('ntlm_auth_domain', ntlm_domain)
        cfg.save('ntlm_auth_user', username)
        cfg.save('ntlm_auth_url', url)

        om.out.debug('Called SetNtlmAuth')

        if not hasattr(self, '_password_mgr'):
            # create a new password manager
            self._password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

        # HTTPNtmlAuthHandler expects username to have the domain name
        # separated with a '\', so that's what we do here:
        username = ntlm_domain + '\\' + username

        self._password_mgr.add_password(None, url, username, password)
        self._ntlmAuthHandler = HTTPNtlmAuthHandler.HTTPNtlmAuthHandler(
            self._password_mgr)

        self.need_update = True

    def build_openers(self):
        om.out.debug('Called build_openers')

        # Instantiate the handlers passing the proxy as parameter
        self._kAHTTP = kAHTTP()
        self._kAHTTPS = kAHTTPS(self.get_proxy())
        self._cache_hdler = CacheHandler()

        # Prepare the list of handlers
        handlers = []
        for handler in [self._proxy_handler, self._basicAuthHandler,
                        self._ntlmAuthHandler, self._cookieHandler,
                        MultipartPostHandler.MultipartPostHandler,
                        self._kAHTTP, self._kAHTTPS, LogHandler,
                        HTTPErrorHandler, HTTP30XHandler,
                        mangleHandler.mangleHandler(self._mangle_plugins),
                        HTTPGzipProcessor, self._url_parameterHandler,
                        self._cache_hdler]:
            if handler:
                handlers.append(handler)

        if cfg.get('ignore_session_cookies'):
            handlers.remove(self._cookieHandler)

        self._uri_opener = urllib2.build_opener(*handlers)

        # Prevent the urllib from putting his user-agent header
        self._uri_opener.addheaders = [('Accept', '*/*')]

    def get_custom_opener(self):
        return self._uri_opener

    def clear_cache(self):
        '''
        Calls the cache handler and requires it to clear the cache, removing
        files and directories.
        
        @return: True if the cache was sucessfully cleared.
        '''
        if self._cache_hdler is not None: 
            return self._cache_hdler.clear()
        
        # The is no cache, clear always is successful in this case
        return True

    def set_mangle_plugins(self, mp):
        '''
        Configure the mangle plugins to be used.

        @param mp: A list of mangle plugin instances.
        '''
        self._mangle_plugins = mp

    def get_mangle_plugins(self):
        return self._mangle_plugins

    def get_max_file_size(self):
        return cfg.get('max_file_size')

    def set_max_file_size(self, fsize):
        cfg.save('max_file_size', fsize)

    def set_max_http_retries(self, retryN):
        cfg.save('max_http_retries', retryN)

    def get_max_retrys(self):
        return cfg.get('max_http_retries')

    def set_url_parameter(self, urlParam):
        # Do some input cleanup/validation
        urlParam = urlParam.replace("'", "")
        urlParam = urlParam.replace("\"", "")
        urlParam = urlParam.lstrip().rstrip()
        if urlParam != '':
            cfg.save('url_parameter', urlParam)
            self._url_parameterHandler = URLParameterHandler(urlParam)

    def get_url_parameter(self):
        return cfg.get('url_parameter')

    def get_options(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'The timeout for connections to the HTTP server'
        h1 = 'Set low timeouts for LAN use and high timeouts for slow Internet connections.'
        o1 = opt_factory('timeout', cfg.get('timeout'), d1, 'integer', help=h1)

        d2 = 'Set the headers filename. This file has additional headers that are added to each request.'
        o2 = opt_factory('headers_file', cfg.get('headers_file'), d2, 'string')

        d3 = 'Set the basic authentication username for HTTP requests'
        o3 = opt_factory('basic_auth_user', cfg.get(
            'basic_auth_user'), d3, 'string', tabid='Basic HTTP Authentication')

        d4 = 'Set the basic authentication password for HTTP requests'
        o4 = opt_factory('basic_auth_passwd', cfg.get(
            'basic_auth_passwd'), d4, 'string', tabid='Basic HTTP Authentication')

        d5 = 'Set the basic authentication domain for HTTP requests'
        h5 = 'This configures on which requests to send the authentication settings configured'
        h5 += ' in basic_auth_passwd and basic_auth_user. If you are unsure, just set it to the'
        h5 += ' target domain name.'
        o5 = opt_factory('basic_auth_domain', cfg.get('basic_auth_domain'), d5,
                         'string', help=h5, tabid='Basic HTTP Authentication')

        d6a = 'Set the NTLM authentication domain (the windows domain name) for HTTP requests'
        o6a = opt_factory('ntlm_auth_domain', cfg.get(
            'ntlm_auth_domain'), d6a, 'string', tabid='NTLM Authentication')

        d6 = 'Set the NTLM authentication username for HTTP requests'
        o6 = opt_factory('ntlm_auth_user', cfg.get(
            'ntlm_auth_user'), d6, 'string', tabid='NTLM Authentication')

        d7 = 'Set the NTLM authentication password for HTTP requests'
        o7 = opt_factory('ntlm_auth_passwd', cfg.get(
            'ntlm_auth_passwd'), d7, 'string', tabid='NTLM Authentication')

        d7b = 'Set the NTLM authentication domain for HTTP requests'
        h7b = 'This configures on which requests to send the authentication settings configured'
        h7b += ' in ntlm_auth_passwd and ntlm_auth_user. If you are unsure, just set it to the'
        h7b += ' target domain name.'
        o7b = opt_factory('ntlm_auth_url', cfg.get(
            'ntlm_auth_url'), d7b, 'string', tabid='NTLM Authentication')

        d8 = 'Set the cookiejar filename.'
        h8 = 'The cookiejar file MUST be in mozilla format.'
        h8 += ' An example of a valid mozilla cookie jar file follows:\n\n'
        h8 += '# Netscape HTTP Cookie File\n'
        h8 += '.domain.com    TRUE   /       FALSE   1731510001      user    admin\n\n'
        h8 += 'The comment IS mandatory. Take special attention to spaces.'
        o8 = opt_factory('cookie_jar_file', cfg.get(
            'cookie_jar_file'), d8, 'string', help=h8, tabid='Cookies')

        d9 = 'Ignore session cookies'
        h9 = 'If set to True, w3af will ignore all session cookies sent by the web application.'
        o9 = opt_factory('ignore_session_cookies', cfg.get(
            'ignore_session_cookies'), d9, 'boolean', help=h9, tabid='Cookies')

        d10 = 'Proxy TCP port'
        h10 = 'TCP port for the remote proxy server to use. On Microsoft Windows systems, w3af'
        h10 += ' will use the proxy settings that are configured in Internet Explorer.'
        o10 = opt_factory('proxy_port', cfg.get(
            'proxy_port'), d10, 'integer', help=h10, tabid='Outgoing proxy')

        d11 = 'Proxy IP address'
        h11 = 'IP address for the remote proxy server to use. On Microsoft Windows systems, w3af'
        h11 += ' will use the proxy settings that are configured in Internet Explorer.'
        o11 = opt_factory('proxy_address', cfg.get(
            'proxy_address'), d11, 'string', help=h11, tabid='Outgoing proxy')

        d12 = 'User Agent header'
        h12 = 'User Agent header to send in request.'
        o12 = opt_factory('user_agent', cfg.get(
            'user_agent'), d12, 'string', help=h12, tabid='Misc')

        d13 = 'Maximum file size'
        h13 = 'Indicates the maximum file size (in bytes) that w3af will GET/POST.'
        o13 = opt_factory('max_file_size', cfg.get(
            'max_file_size'), d13, 'integer', help=h13, tabid='Misc')

        d14 = 'Maximum number of retries'
        h14 = 'Indicates the maximum number of retries when requesting an URL.'
        o14 = opt_factory('max_http_retries', cfg.get(
            'max_http_retries'), d14, 'integer', help=h14, tabid='Misc')

        d15 = 'A comma separated list that determines what URLs will ALWAYS be detected as 404 pages.'
        o15 = opt_factory('always_404', cfg.get(
            'always_404'), d15, 'list', tabid='404 settings')

        d16 = 'A comma separated list that determines what URLs will NEVER be detected as 404 pages.'
        o16 = opt_factory('never_404', cfg.get(
            'never_404'), d16, 'list', tabid='404 settings')

        d17 = 'If this string is found in an HTTP response, then it will be tagged as a 404.'
        o17 = opt_factory('string_match_404', cfg.get(
            'string_match_404'), d17, 'string', tabid='404 settings')

        d18 = 'Append the given URL parameter to every accessed URL.'
        d18 += ' Example: http://www.foobar.com/index.jsp;<parameter>?id=2'
        o18 = opt_factory(
            'url_parameter', cfg.get('url_parameter'), d18, 'string')

        ol = OptionList()
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

    def set_options(self, options_list):
        '''
        This method sets all the options that are configured using the user interface
        generated by the framework using the result of get_options().

        @param options_list: An OptionList with the option objects for a plugin.
        @return: No value is returned.
        '''
        getOptsMapValue = lambda n: options_list[n].get_value()
        self.set_timeout(getOptsMapValue('timeout'))

        # Only apply changes if they exist
        bAuthDomain = getOptsMapValue('basic_auth_domain')
        bAuthUser = getOptsMapValue('basic_auth_user')
        bAuthPass = getOptsMapValue('basic_auth_passwd')

        if bAuthDomain != cfg['basic_auth_domain'] or \
            bAuthUser != cfg['basic_auth_user'] or \
                bAuthPass != cfg['basic_auth_passwd']:
            try:
                bAuthDomain = URL(bAuthDomain) if bAuthDomain else ''
            except ValueError:
                bAuthDomain = None

            self.set_basic_auth(bAuthDomain, bAuthUser, bAuthPass)

        ntlm_auth_domain = getOptsMapValue('ntlm_auth_domain')
        ntlm_auth_user = getOptsMapValue('ntlm_auth_user')
        ntlm_auth_passwd = getOptsMapValue('ntlm_auth_passwd')
        ntlm_auth_url = getOptsMapValue('ntlm_auth_url')

        if ntlm_auth_domain != cfg['ntlm_auth_domain'] or \
            ntlm_auth_user != cfg['ntlm_auth_user'] or \
            ntlm_auth_passwd != cfg['ntlm_auth_passwd'] or \
                ntlm_auth_url != cfg['ntlm_auth_url']:
            self.set_ntlm_auth(
                ntlm_auth_url, ntlm_auth_domain, ntlm_auth_user, ntlm_auth_passwd)

        # Only apply changes if they exist
        proxy_address = getOptsMapValue('proxy_address')
        proxy_port = getOptsMapValue('proxy_port')

        if proxy_address != cfg['proxy_address'] or \
                proxy_port != cfg['proxy_port']:
            self.set_proxy(proxy_address, proxy_port)

        self.set_cookie_jar_file(getOptsMapValue('cookie_jar_file'))
        self.set_headers_file(getOptsMapValue('headers_file'))
        self.set_user_agent(getOptsMapValue('user_agent'))
        cfg['ignore_session_cookies'] = getOptsMapValue('ignore_session_cookies')

        self.set_max_file_size(getOptsMapValue('max_file_size'))
        self.set_max_http_retries(getOptsMapValue('max_http_retries'))

        self.set_url_parameter(getOptsMapValue('url_parameter'))

        # 404 settings are saved here
        cfg['never_404'] = getOptsMapValue('never_404')
        cfg['always_404'] = getOptsMapValue('always_404')
        cfg['string_match_404'] = getOptsMapValue('string_match_404')

    def get_desc(self):
        return ('This section is used to configure URL settings that '
                'affect the core and all plugins.')
