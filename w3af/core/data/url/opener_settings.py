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
import urlparse
import cookielib

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.configurable import Configurable
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.kb.config import cf as cfg
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.constants import MAX_HTTP_RETRIES, USER_AGENT
from w3af.core.data.url.director import CustomOpenerDirector, build_opener
from w3af.core.data.url.handlers.ntlm_auth import HTTPNtlmAuthHandler
from w3af.core.data.url.handlers.fast_basic_auth import FastHTTPBasicAuthHandler
from w3af.core.data.url.handlers.cookie_handler import CookieHandler
from w3af.core.data.url.handlers.gzip_handler import HTTPGzipProcessor
from w3af.core.data.url.handlers.keepalive import HTTPHandler
from w3af.core.data.url.handlers.keepalive import HTTPSHandler
from w3af.core.data.url.handlers.output_manager import OutputManagerHandler
from w3af.core.data.url.handlers.redirect import HTTP30XHandler
from w3af.core.data.url.handlers.url_parameter import URLParameterHandler
from w3af.core.data.url.handlers.cache import CacheHandler
from w3af.core.data.url.handlers.blacklist import BlacklistHandler
from w3af.core.data.url.handlers.mangle import MangleHandler
from w3af.core.data.url.handlers.normalize import NormalizeHandler
from w3af.core.data.url.handlers.errors import ErrorHandler, NoOpErrorHandler
from w3af.core.data.options.option_types import POSITIVE_INT, INT, STRING, URL_LIST, BOOL
from w3af.core.data.misc.cookie_jar import ImprovedMozillaCookieJar


USER_AGENT_HEADER = 'User-Agent'


class OpenerSettings(Configurable):
    """
    This is a urllib2 configuration manager.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):

        # Set the openers to None
        self._basic_auth_handler = None
        self._proxy_handler = None
        self._ka_http = None
        self._ka_https = None
        self._url_parameter_handler = None
        self._ntlm_auth_handler = None
        self._cache_handler = None
        self._password_mgr = None
        # Keep alive handlers are created on build_openers()

        cj = ImprovedMozillaCookieJar()
        self._cookie_handler = CookieHandler(cj)

        # Openers
        self._uri_opener = None

        # Some internal variables
        self.need_update = True
        
        # to use random Agent in http requests
        self.rand_user_agent = False
        
        #   which basically is the UA for IE8 running in Windows 7, plus our
        #   website :)    
        self.header_list = [(USER_AGENT_HEADER, USER_AGENT)]
                
        # By default, don't mangle any request/responses
        self._mangle_plugins = []

        # User configured variables
        if cfg.get('user_agent') is None:
            # This is the first time we are executed...
            self.set_default_values()

    def set_default_values(self):
        cfg.save('configured_timeout', 0)
        cfg.save('headers_file', '')
        cfg.save('cookie_jar_file', '')
        cfg.save('user_agent', 'w3af.org')
        cfg.save('rand_user_agent', False)

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
        cfg.save('max_http_retries', MAX_HTTP_RETRIES)
        cfg.save('max_requests_per_second', 0)

        cfg.save('url_parameter', '')

        # 404 settings
        cfg.save('never_404', [])
        cfg.save('always_404', [])
        cfg.save('string_match_404', '')

    def set_headers_file(self, headers_file):
        """
        Sets the special headers to use, this headers are specified in a file by
        the user. The file can have multiple lines, each line should have the
        following structure :
            - HEADER:VALUE_OF_HEADER

        :param headers_file: The filename where the additional headers are
                             specified
        :return: No value is returned.
        """
        if not headers_file:
            return

        try:
            f = open(headers_file, 'r')
        except:
            msg = 'Unable to open headers file: "%s"'
            raise BaseFrameworkException(msg % headers_file)

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
            om.out.debug('Added the following header: "%s: %s"' % (h, v))

    def close_connections(self):
        handlers = (self._ka_http, self._ka_https)
        for handler in handlers:
            if handler is not None:
                handler.close_all()

    def get_headers_file(self):
        return cfg.get('headers_file')

    def set_cookie_jar_file(self, cookiejar_file):
        om.out.debug('Called set_cookie_jar_file')

        if not cookiejar_file:
            return

        cj = ImprovedMozillaCookieJar()

        try:
            cj.load(cookiejar_file)
        except cookielib.LoadError, cle:
            # pylint: disable=E1101
            if cle.message.startswith('invalid Netscape format cookies file'):
                docs_url = ('http://docs.w3af.org/en/latest/'
                            'authentication.html#setting-http-cookie')

                msg = ('The supplied cookiejar file is not in Netscape format'
                       ' please review our documentation at %s to better'
                       ' understand the required format.')

                raise BaseFrameworkException(msg % docs_url)
            else:
                msg = 'Error while loading cookiejar file. Description: "%s".'
                raise BaseFrameworkException(msg % cle)
            # pylint: enable=E1101
        except IOError:
            msg = 'The specified cookie jar file does not exist.'
            raise BaseFrameworkException(msg)
        else:
            self._cookie_handler = CookieHandler(cj)
            cfg.save('cookie_jar_file', cookiejar_file)
            
            if not len(cj):
                msg = ('Did not load any cookies from the cookie jar file.'
                       ' This usually happens when there are no cookies in'
                       ' the file, the cookies have expired or the file is not'
                       ' in the expected format.')
                raise BaseFrameworkException(msg)
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
        self._cookie_handler.clear_cookies()

    def set_configured_timeout(self, timeout):
        """
        :param timeout: User configured timeout setting. 0 means enable the auto
                        timeout adjust feature.
        :return: None
        """
        if timeout < 0 or timeout > 30:
            err = 'The timeout parameter should be between 0 and 30 seconds.'
            raise BaseFrameworkException(err)

        cfg.save('configured_timeout', timeout)

    def get_configured_timeout(self):
        """
        :return: The user configured setting for timeout
        """
        return cfg.get('configured_timeout')

    def set_user_agent(self, user_agent):
        self.header_list = [i for i in self.header_list if i[0].lower()
                            != USER_AGENT_HEADER]
        self.header_list.append((USER_AGENT_HEADER, user_agent))
        cfg.save('user_agent', user_agent)
        
    def set_rand_user_agent(self, rand_user_agent):
        om.out.debug('Called set_rand_user_agent')
        self.rand_user_agent = rand_user_agent
        cfg.save('rand_user_agent', rand_user_agent)
        
    def get_user_agent(self):
        return cfg.get('user_agent')
    
    def get_rand_user_agent(self):
        return cfg.get('rand_user_agent')

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

        proxy_url = 'http://%s:%s' % (ip, port)
        proxy_map = {'http': proxy_url}
        self._proxy_handler = urllib2.ProxyHandler(proxy_map)

    def get_proxy(self):
        return cfg.get('proxy_address') + ':' + str(cfg.get('proxy_port'))

    def set_basic_auth(self, url, username, password):
        om.out.debug('Called set_basic_auth')

        if not url:
            if url is None:
                raise BaseFrameworkException('The entered basic_auth_domain'
                                             ' URL is invalid!')
            elif username or password:
                msg = ('To properly configure the basic authentication'
                       ' settings, you should also set the auth domain. If you '
                       ' are unsure, you can set it to the target domain name'
                       ' (eg. www.target.com)')
                raise BaseFrameworkException(msg)
        else:
            if not hasattr(self, '_password_mgr'):
                # Create a new password manager
                self._password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

            # Add the username and password
            domain = url.get_domain()
            self._password_mgr.add_password(None, domain, username, password)
            self._basic_auth_handler = FastHTTPBasicAuthHandler(self._password_mgr)

            self.need_update = True

        # Save'em!
        cfg.save('basic_auth_passwd', password)
        cfg.save('basic_auth_user', username)
        cfg.save('basic_auth_domain', url)

    def get_basic_auth(self):
        basic_auth_domain = cfg.get('basic_auth_domain')
        scheme, domain, path, x1, x2, x3 = urlparse.urlparse(basic_auth_domain)

        fmt = '%s://%s:%s@%s/'

        return fmt % (scheme,
                      cfg.get('basic_auth_user'),
                      cfg.get('basic_auth_passwd'),
                      domain)

    def set_ntlm_auth(self, url, ntlm_domain, username, password):
        cfg.save('ntlm_auth_passwd', password)
        cfg.save('ntlm_auth_domain', ntlm_domain)
        cfg.save('ntlm_auth_user', username)
        cfg.save('ntlm_auth_url', url)

        if not hasattr(self, '_password_mgr'):
            # create a new password manager
            self._password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

        # HTTPNtmlAuthHandler expects username to have the domain name
        # separated with a '\', so that's what we do here:
        username = ntlm_domain + '\\' + username

        self._password_mgr.add_password(None, url, username, password)
        self._ntlm_auth_handler = HTTPNtlmAuthHandler(self._password_mgr)

        self.need_update = True

    def build_openers(self):
        # Instantiate the handlers passing the proxy as parameter
        self._ka_http = HTTPHandler()
        self._ka_https = HTTPSHandler(self.get_proxy())
        self._cache_handler = CacheHandler()

        # Prepare the list of handlers
        handlers = []
        for handler in [self._proxy_handler,
                        self._basic_auth_handler,
                        self._ntlm_auth_handler,
                        self._cookie_handler,
                        NormalizeHandler,
                        self._ka_http,
                        self._ka_https,
                        OutputManagerHandler,
                        HTTP30XHandler,
                        BlacklistHandler,
                        MangleHandler(self._mangle_plugins),
                        HTTPGzipProcessor,
                        self._url_parameter_handler,
                        self._cache_handler,
                        ErrorHandler,
                        NoOpErrorHandler]:
            if handler:
                handlers.append(handler)

        if cfg.get('ignore_session_cookies'):
            handlers.remove(self._cookie_handler)

        self._uri_opener = build_opener(CustomOpenerDirector, handlers)

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
        if self._cache_handler is not None:
            return self._cache_handler.clear()
        
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

    def set_max_file_size(self, max_file_size):
        cfg.save('max_file_size', max_file_size)

    def set_max_http_retries(self, retry_num):
        cfg.save('max_http_retries', retry_num)

    def set_max_requests_per_second(self, max_requests_per_second):
        cfg.save('max_requests_per_second', max_requests_per_second)

    def get_max_requests_per_second(self):
        return cfg.get('max_requests_per_second')

    def get_max_retrys(self):
        return cfg.get('max_http_retries')

    def set_url_parameter(self, url_param):
        # Do some input cleanup/validation
        url_param = url_param.replace("'", "")
        url_param = url_param.replace("\"", "")
        url_param = url_param.lstrip().rstrip()

        if url_param:
            cfg.save('url_parameter', url_param)
            self._url_parameter_handler = URLParameterHandler(url_param)

    def get_url_parameter(self):
        return cfg.get('url_parameter')

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()
        
        d = 'HTTP connection timeout'
        h = 'The default value of zero indicates that the timeout will be' \
            ' auto-adjusted based on the average response times from the' \
            ' application. When set to a value different than zero it is' \
            ' the number of seconds to wait for a response form the server' \
            ' before timing out. Set low timeouts for LAN use and high' \
            ' timeouts for slow Internet connections.'
        o = opt_factory('timeout', cfg.get('configured_timeout'), d, INT,
                        help=h)
        ol.add(o)
        
        d = 'HTTP headers filename which contains additional headers to be' \
            ' added in each request'
        o = opt_factory('headers_file', cfg.get('headers_file'), d, STRING)
        ol.add(o)
        
        d = 'Basic authentication username'
        o = opt_factory('basic_auth_user', cfg.get('basic_auth_user'), d,
                        STRING, tabid='Basic HTTP Authentication')
        ol.add(o)
        
        d = 'Basic authentication password'
        o = opt_factory('basic_auth_passwd', cfg.get('basic_auth_passwd'), d,
                        STRING, tabid='Basic HTTP Authentication')
        ol.add(o)
        
        d = 'Basic authentication domain'
        h = ('This configures on which requests to send the authentication'
             ' settings configured in basic_auth_passwd and basic_auth_user.'
             ' If you are unsure, just set it to the target domain name.')
        o = opt_factory('basic_auth_domain', cfg.get('basic_auth_domain'), d,
                        STRING, help=h, tabid='Basic HTTP Authentication')
        ol.add(o)
        
        d = 'NTLM authentication domain (windows domain name)'
        h = 'Note that only NTLM v1 is supported.'
        o = opt_factory('ntlm_auth_domain', cfg.get('ntlm_auth_domain'), d,
                        STRING, help=h, tabid='NTLM Authentication')
        ol.add(o)
        
        d = 'NTLM authentication username'
        o = opt_factory('ntlm_auth_user', cfg.get('ntlm_auth_user'), d,
                        STRING, tabid='NTLM Authentication')
        ol.add(o)
        
        d = 'NTLM authentication password'
        o = opt_factory('ntlm_auth_passwd', cfg.get('ntlm_auth_passwd'),
                        d, STRING, tabid='NTLM Authentication')
        ol.add(o)
        
        d = 'NTLM authentication domain (target domain name)'
        h = 'This configures on which requests to send the authentication'\
            ' settings configured in ntlm_auth_passwd and ntlm_auth_user.'\
            ' If you are unsure, just set it to the target domain name.'
        o = opt_factory('ntlm_auth_url', cfg.get('ntlm_auth_url'), d,
                        STRING, tabid='NTLM Authentication', help=h)
        ol.add(o)
        
        d = 'Cookie Jar file holding HTTP cookies'
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
                        STRING, help=h, tabid='Cookies')
        ol.add(o)
        
        d = 'Ignore session cookies'
        h = ('If set to True, w3af will not extract cookies from HTTP responses'
             ' nor send HTTP cookies in requests.')
        o = opt_factory('ignore_session_cookies',
                        cfg.get('ignore_session_cookies'), d, 'boolean',
                        help=h, tabid='Cookies')
        ol.add(o)
        
        d = 'Proxy TCP port'
        h = 'TCP port for the HTTP proxy. On Microsoft Windows systems,'\
            ' w3af will use Internet Explorer\'s proxy settings'
        o = opt_factory('proxy_port', cfg.get('proxy_port'), d, INT,
                        help=h, tabid='Outgoing proxy')
        ol.add(o)
        
        d = 'Proxy IP address'
        h = 'IP address for the HTTP proxy. On Microsoft Windows systems,'\
            ' w3af will use Internet Explorer\'s proxy settings'
        o = opt_factory('proxy_address', cfg.get('proxy_address'), d,
                        STRING, help=h, tabid='Outgoing proxy')
        ol.add(o)
        
        d = 'User Agent header'
        h = 'User Agent header to send in HTTP requests'
        o = opt_factory('user_agent', cfg.get('user_agent'), d, STRING,
                        help=h, tabid='Misc')
        ol.add(o)

        d = 'Use random User-Agent header'
        h = 'Enable to make w3af choose a random user agent for each HTTP'\
            ' request sent to the target web application'
        o = opt_factory('rand_user_agent', cfg.get('rand_user_agent'), d, BOOL,
                        help=h, tabid='Misc')
        ol.add(o)

        d = 'Maximum file size'
        h = 'Indicates the maximum file size (in bytes) that w3af will'\
            ' retrieve from the remote server'
        o = opt_factory('max_file_size', cfg.get('max_file_size'), d,
                        INT, help=h, tabid='Misc')
        ol.add(o)
        
        d = 'Maximum number of HTTP request retries'
        h = 'Indicates the maximum number of retries when requesting an URL'
        o = opt_factory('max_http_retries', cfg.get('max_http_retries'), d,
                        INT, help=h, tabid='Misc')
        ol.add(o)

        d = 'Maximum HTTP requests per second'
        h = 'Indicates the maximum HTTP requests per second to send. A value' \
            ' of zero indicates no limit'
        o = opt_factory('max_requests_per_second',
                        cfg.get('max_requests_per_second'), d, POSITIVE_INT,
                        help=h, tabid='Misc')
        ol.add(o)

        d = ('Comma separated list of URLs which will always be detected as'
             ' 404 pages')
        o = opt_factory('always_404', cfg.get('always_404'), d, URL_LIST,
                        tabid='404 settings')
        ol.add(o)
        
        d = ('Comma separated list of URLs which will never be detected as'
             ' 404 pages')
        o = opt_factory('never_404', cfg.get('never_404'), d, URL_LIST,
                        tabid='404 settings')
        ol.add(o)
        
        d = 'Tag HTTP response as 404 if the string is found in it\'s body'
        o = opt_factory('string_match_404', cfg.get('string_match_404'), d,
                        STRING, tabid='404 settings')
        ol.add(o)

        d = 'URL parameter (http://host.tld/path;<parameter>)'
        h = 'Appends the given URL parameter to every accessed URL.'\
            ' Example: http://www.foobar.com/index.jsp;<parameter>?id=2'
        o = opt_factory('url_parameter', cfg.get('url_parameter'), d,
                        STRING, help=h)
        ol.add(o)
        
        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: An OptionList with the option objects for a plugin.
        :return: No value is returned.
        """
        get_opt_value = lambda n: options_list[n].get_value()
        self.set_configured_timeout(get_opt_value('timeout'))

        # Only apply changes if they exist
        bauth_domain = get_opt_value('basic_auth_domain')
        bauth_user = get_opt_value('basic_auth_user')
        bauth_pass = get_opt_value('basic_auth_passwd')

        if bauth_domain != cfg['basic_auth_domain'] or \
        bauth_user != cfg['basic_auth_user'] or \
        bauth_pass != cfg['basic_auth_passwd']:
            try:
                bauth_domain = URL(bauth_domain) if bauth_domain else ''
            except ValueError:
                bauth_domain = None

            self.set_basic_auth(bauth_domain, bauth_user, bauth_pass)

        ntlm_auth_domain = get_opt_value('ntlm_auth_domain')
        ntlm_auth_user = get_opt_value('ntlm_auth_user')
        ntlm_auth_passwd = get_opt_value('ntlm_auth_passwd')
        ntlm_auth_url = get_opt_value('ntlm_auth_url')

        if ntlm_auth_domain != cfg['ntlm_auth_domain'] or \
        ntlm_auth_user != cfg['ntlm_auth_user'] or \
        ntlm_auth_passwd != cfg['ntlm_auth_passwd'] or \
        ntlm_auth_url != cfg['ntlm_auth_url']:
            self.set_ntlm_auth(ntlm_auth_url, ntlm_auth_domain,
                               ntlm_auth_user, ntlm_auth_passwd)

        # Only apply changes if they exist
        proxy_address = get_opt_value('proxy_address')
        proxy_port = get_opt_value('proxy_port')

        if proxy_address != cfg['proxy_address'] or \
        proxy_port != cfg['proxy_port']:
            self.set_proxy(proxy_address, proxy_port)

        self.set_cookie_jar_file(get_opt_value('cookie_jar_file'))
        self.set_headers_file(get_opt_value('headers_file'))
        self.set_user_agent(get_opt_value('user_agent'))
        self.set_rand_user_agent(get_opt_value('rand_user_agent'))
        cfg['ignore_session_cookies'] = get_opt_value('ignore_session_cookies')

        self.set_max_file_size(get_opt_value('max_file_size'))
        self.set_max_http_retries(get_opt_value('max_http_retries'))
        self.set_max_requests_per_second(get_opt_value('max_requests_per_second'))

        self.set_url_parameter(get_opt_value('url_parameter'))

        # 404 settings are saved here
        cfg['never_404'] = get_opt_value('never_404')
        cfg['always_404'] = get_opt_value('always_404')
        cfg['string_match_404'] = get_opt_value('string_match_404')

    def get_desc(self):
        return ('This section is used to configure URL settings that '
                'affect the core and plugins.')
