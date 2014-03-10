"""
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

"""
import urllib2
import socket
import urlparse
import cookielib

import w3af.core.controllers.output_manager as om
import w3af.core.data.url.handlers.ntlm_auth as HTTPNtlmAuthHandler

from w3af.core.controllers.configurable import Configurable
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.kb.config import cf as cfg
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.parsers.url import URL

from w3af.core.data.url.handlers.fast_basic_auth import FastHTTPBasicAuthHandler
from w3af.core.data.url.handlers.cookie_handler import CookieHandler
from w3af.core.data.url.handlers.gzip_handler import HTTPGzipProcessor
from w3af.core.data.url.handlers.keepalive import HTTPHandler as kAHTTP
from w3af.core.data.url.handlers.keepalive import HTTPSHandler as kAHTTPS
from w3af.core.data.url.handlers.output_manager import OutputManagerHandler
from w3af.core.data.url.handlers.redirect import HTTP30XHandler
from w3af.core.data.url.handlers.url_parameter import URLParameterHandler
from w3af.core.data.url.handlers.cache import CacheHandler
from w3af.core.data.url.handlers.blacklist import BlacklistHandler 
from w3af.core.data.url.handlers.mangle import MangleHandler
from w3af.core.data.url.handlers.multipart import MultipartPostHandler
from w3af.core.data.url.handlers.normalize import NormalizeHandler
from w3af.core.data.url.handlers.errors import ErrorHandler


class OpenerSettings(Configurable):
    """
    This is a urllib2 configuration manager.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):

        # Set the openers to None
        self._basicAuthHandler = None
        self._proxy_handler = None
        self._kAHTTP = None
        self._kAHTTPS = None
        self._url_parameterHandler = None
        self._ntlmAuthHandler = None
        self._cache_hdler = None
        # Keep alive handlers are created on build_openers()

        cj = cookielib.MozillaCookieJar()
        self._cookie_handler = CookieHandler(cj)

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
        user_agent = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1;'\
                     ' Trident/4.0; w3af.org)'
        #   which basically is the UA for IE8 running in Windows 7, plus our
        #   website :)
        self.header_list = [('User-Agent', user_agent)]

        # By default, don't mangle any request/responses
        self._mangle_plugins = []

        # User configured variables
        if cfg.get('timeout') is None:
            # This is the first time we are executed...
            self.set_default_values()
    
    def set_default_values(self):
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
        """
        Sets the special headers to use, this headers are specified in a file by the user.
        The file can have multiple lines, each line should have the following structure :
            - HEADER:VALUE_OF_HEADER

        :param headers_file: The filename where the special headers are specified.
        :return: No value is returned.
        """
        om.out.debug('Called SetHeaders()')
        if headers_file != '':
            try:
                f = open(headers_file, 'r')
            except:
                raise BaseFrameworkException(
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
        """
        :param header_list: A list of tuples with (header,value) to be added
                            to every request.
        :return: nothing
        """
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

    def set_cookie_jar_file(self, cookiejar_file):
        om.out.debug('Called SetCookie')

        if not cookiejar_file:
            return
        
        cj = cookielib.MozillaCookieJar()
        try:
            cj.load(cookiejar_file)
        except Exception, e:
            msg = 'Error while loading cookiejar file. Description: "%s".'
            raise BaseFrameworkException(msg % e)
        else:
            self._cookie_handler = CookieHandler(cj)
            cfg.save('cookie_jar_file', cookiejar_file)
            
            if not len(cj):
                msg = 'Did not load any cookies from the cookie jar file.'\
                      ' This usually happens when there are no cookies in'\
                      ' the file or the cookies have expired.'
                om.out.error(msg)
            else:
                om.out.debug('Loaded the following cookies:')
                for c in cj:
                    om.out.debug(str(c))

    def get_cookie_jar_file(self):
        return cfg.get('cookie_jar_file')

    def get_cookies(self):
        """
        :return: The cookies that were collected during this scan.
        """
        return self._cookie_handler.cookiejar
    
    def clear_cookies(self):
        self._cookie_handler.cookiejar.clear()
        self._cookie_handler.cookiejar.clear_session_cookies()

    def set_timeout(self, timeout):
        om.out.debug('Called set_timeout(%s)' % timeout)
        if timeout > 60 or timeout < 1:
            err = 'The timeout parameter should be between 1 and 60 seconds.'
            raise BaseFrameworkException(err)
        else:
            cfg.save('timeout', timeout)

            # Set the default timeout
            # I don't need to use timeoutsocket.py , it has been added to
            # python sockets!
            socket.setdefaulttimeout(cfg.get('timeout'))
            
            self.need_update = True

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
        """
        Saves the proxy information and creates the handler.

        If the information is invalid it will set self._proxy_handler to None,
        so no proxy is used.

        :return: None
        """
        om.out.debug('Called set_proxy(%s, %s)' % (ip, port))

        if not ip:
            #    The user doesn't want a proxy anymore
            cfg.save('proxy_address', '')
            cfg.save('proxy_port', port)
            self._proxy_handler = None
            return

        if port > 65535 or port < 1:
            #    The user entered something invalid
            self._proxy_handler = None
            raise BaseFrameworkException('Invalid port number: ' + str(port))

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
                raise BaseFrameworkException(
                    'The entered basic_auth_domain URL is invalid!')
            elif username or password:
                msg = ('To properly configure the basic authentication '
                       'settings, you should also set the auth domain. If you '
                       'are unsure, you can set it to the target domain name.')
                raise BaseFrameworkException(msg)
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
                        self._ntlmAuthHandler, self._cookie_handler,
                        MultipartPostHandler, NormalizeHandler,
                        self._kAHTTP, self._kAHTTPS, OutputManagerHandler,
                        HTTP30XHandler, BlacklistHandler,
                        MangleHandler(self._mangle_plugins),
                        HTTPGzipProcessor, self._url_parameterHandler,
                        self._cache_hdler, ErrorHandler]:
            if handler:
                handlers.append(handler)

        if cfg.get('ignore_session_cookies'):
            handlers.remove(self._cookie_handler)

        self._uri_opener = urllib2.build_opener(*handlers)

        # Prevent the urllib from putting his user-agent header
        self._uri_opener.addheaders = [('Accept', '*/*')]

    def get_custom_opener(self):
        return self._uri_opener

    def clear_cache(self):
        """
        Calls the cache handler and requires it to clear the cache, removing
        files and directories.
        
        :return: True if the cache was successfully cleared.
        """
        if self._cache_hdler is not None:
            return self._cache_hdler.clear()
        
        # The is no cache, clear always is successful in this case
        return True

    def set_mangle_plugins(self, mp):
        """
        Configure the mangle plugins to be used.

        :param mp: A list of mangle plugin instances.
        """
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
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()
        
        d = 'The timeout for connections to the HTTP server'
        h = 'Set low timeouts for LAN use and high timeouts for slow Internet'\
             ' connections.'
        o = opt_factory('timeout', cfg.get('timeout'), d, 'integer', help=h)
        ol.add(o)
        
        d = 'Set the headers filename. This file has additional headers which'\
            ' are added to each request.'
        o = opt_factory('headers_file', cfg.get('headers_file'), d, 'string')
        ol.add(o)
        
        d = 'Set the basic authentication username for HTTP requests'
        o = opt_factory('basic_auth_user', cfg.get('basic_auth_user'), d,
                        'string', tabid='Basic HTTP Authentication')
        ol.add(o)
        
        d = 'Set the basic authentication password for HTTP requests'
        o = opt_factory('basic_auth_passwd', cfg.get('basic_auth_passwd'), d,
                        'string', tabid='Basic HTTP Authentication')
        ol.add(o)
        
        d = 'Set the basic authentication domain for HTTP requests'
        h = 'This configures on which requests to send the authentication'\
            ' settings configured in basic_auth_passwd and basic_auth_user.'\
            ' If you are unsure, just set it to the target domain name.'
        o = opt_factory('basic_auth_domain', cfg.get('basic_auth_domain'), d,
                        'string', help=h, tabid='Basic HTTP Authentication')
        ol.add(o)
        
        d = 'Set the NTLM authentication domain (the windows domain name)'\
            ' for HTTP requests. Please note that only NTLM v1 is supported.'
        o = opt_factory('ntlm_auth_domain', cfg.get('ntlm_auth_domain'), d,
                        'string', tabid='NTLM Authentication')
        ol.add(o)
        
        d = 'Set the NTLM authentication username for HTTP requests'
        o = opt_factory('ntlm_auth_user', cfg.get('ntlm_auth_user'), d,
                        'string', tabid='NTLM Authentication')
        ol.add(o)
        
        d = 'Set the NTLM authentication password for HTTP requests'
        o = opt_factory('ntlm_auth_passwd', cfg.get('ntlm_auth_passwd'),
                        d, 'string', tabid='NTLM Authentication')
        ol.add(o)
        
        d = 'Set the NTLM authentication domain for HTTP requests'
        h = 'This configures on which requests to send the authentication'\
            ' settings configured in ntlm_auth_passwd and ntlm_auth_user.'\
            ' If you are unsure, just set it to the target domain name.'
        o = opt_factory('ntlm_auth_url', cfg.get('ntlm_auth_url'), d,
                        'string', tabid='NTLM Authentication', help=h)
        ol.add(o)
        
        d = 'Cookie jar file to load cookies from'
        h = 'The cookiejar file MUST be in Mozilla format. An example of a'\
            ' valid Mozilla cookie jar file follows:\n\n'\
            '# Netscape HTTP Cookie File\n'\
            '.domain.com    TRUE   /       FALSE   1731510001'\
            '      user    admin\n\n'\
            'Please note that the comment is mandatory and the fields need'\
            ' to be separated using tabs.\n\n'\
            'It is also important to note that loaded cookies will only be'\
            ' sent if all conditions are met. For example, secure cookies'\
            ' will only be sent over HTTPS and cookie expiration time will'\
            ' influence if a cookie is sent or not.\n\n'\
            'Remember: Session cookies which are stored in cookie jars have'\
            ' their session expiration set to 0, which will prevent them from'\
            ' being sent.'
        o = opt_factory('cookie_jar_file', cfg.get('cookie_jar_file'), d,
                        'string', help=h, tabid='Cookies')
        ol.add(o)
        
        d = 'Ignore session cookies'
        h = 'If set to True, w3af will ignore all session cookies sent by'\
             ' the web application.'
        o = opt_factory('ignore_session_cookies',
                        cfg.get('ignore_session_cookies'), d, 'boolean',
                        help=h, tabid='Cookies')
        ol.add(o)
        
        d = 'Proxy TCP port'
        h = 'TCP port for the HTTP proxy. On Microsoft Windows systems,'\
            ' w3af will use Internet Explorer\'s proxy settings.'
        o = opt_factory('proxy_port', cfg.get('proxy_port'), d, 'integer',
                        help=h, tabid='Outgoing proxy')
        ol.add(o)
        
        d = 'Proxy IP address'
        h = 'IP address for the HTTP proxy. On Microsoft Windows systems,'\
            ' w3af will use Internet Explorer\'s proxy settings.'
        o = opt_factory('proxy_address', cfg.get('proxy_address'), d,
                        'string', help=h, tabid='Outgoing proxy')
        ol.add(o)
        
        d = 'User Agent header'
        h = 'User Agent header to send in HTTP requests.'
        o = opt_factory('user_agent', cfg.get('user_agent'), d, 'string',
                          help=h, tabid='Misc')
        ol.add(o)
        
        d = 'Maximum file size'
        h = 'Indicates the maximum file size (in bytes) that w3af will'\
            ' retrieve from the remote server.'
        o = opt_factory('max_file_size', cfg.get('max_file_size'), d,
                        'integer', help=h, tabid='Misc')
        ol.add(o)
        
        d = 'Maximum number of retries'
        h = 'Indicates the maximum number of retries when requesting an URL.'
        o = opt_factory('max_http_retries', cfg.get('max_http_retries'), d,
                        'integer', help=h, tabid='Misc')
        ol.add(o)
        
        d = 'A comma separated list that determines what URLs will ALWAYS'\
            ' be detected as 404 pages.'
        o = opt_factory('always_404', cfg.get('always_404'), d, 'list',
                        tabid='404 settings')
        ol.add(o)
        
        d = 'A comma separated list that determines what URLs will NEVER be'\
            ' detected as 404 pages.'
        o = opt_factory('never_404', cfg.get('never_404'), d, 'list',
                          tabid='404 settings')
        ol.add(o)
        
        d = 'If this string is found in an HTTP response, then it will be'\
            ' tagged as a 404.'
        o = opt_factory('string_match_404', cfg.get('string_match_404'), d,
                          'string', tabid='404 settings')
        ol.add(o)
        
        d = 'Append the given URL parameter to every accessed URL.'\
              ' Example: http://www.foobar.com/index.jsp;<parameter>?id=2'
        o = opt_factory('url_parameter', cfg.get('url_parameter'), d,
                        'string')
        ol.add(o)
        
        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user interface
        generated by the framework using the result of get_options().

        :param options_list: An OptionList with the option objects for a plugin.
        :return: No value is returned.
        """
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
            self.set_ntlm_auth(ntlm_auth_url, ntlm_auth_domain,
                               ntlm_auth_user, ntlm_auth_passwd)

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
