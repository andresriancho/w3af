'''
collect_cookies.py

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
import Cookie

import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.controllers.plugins.grep_plugin import GrepPlugin
from core.controllers.misc.groupbyMinKey import groupbyMinKey


class collect_cookies(GrepPlugin):
    '''
    Grep every response for session cookies sent by the web application.
      
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    COOKIE_HEADERS = ('set-cookie', 'cookie', 'cookie2')

    COOKIE_FINGERPRINT = (
            ('st8id=','Teros web application firewall'),
            ('ASINFO=','F5 TrafficShield'),
            ('NCI__SessionId=','Netcontinuum'),
                    
            # oracle
            ('$OC4J_','Oracle container for java'),
                    
            # Java
            ('JSESSIONID=','Jakarta Tomcat / Apache'),
            ('JServSessionIdroot=','Apache JServ'),
                    
            # ASP
            ('ASPSESSIONID','ASP'),
            ('ASP.NET_SessionId=','ASP.NET'),
            ('cadata=; path=/; expires=Thu, 01-Jan-1970 00:00:00 GMT',
                                                    'Outlook Web Access'),
                    
            # PHP
            ('PHPSESSID=','PHP'),
                    
            # SAP
            ('sap-usercontext=sap-language=','SAP'),
                    
            # Others
            ('WebLogicSession=','BEA Logic'),
            ('SaneID=','Sane NetTracker'),
            ('ssuid=','Vignette'),
            ('vgnvisitor=','Vignette'),
            ('SESSION_ID=','IBM Net.Commerce'),
            ('NSES40Session=','Netscape Enterprise Server'),
            ('iPlanetUserId=','iPlanet'),
            ('RMID=','RealMedia OpenADStream'),
            ('cftoken=','Coldfusion'),
            ('PORTAL-PSJSESSIONID=','PeopleSoft'),
            ('WEBTRENDS_ID=','WebTrends'),
            ('sesessionid=','IBM WebSphere'),
            ('CGISESSID=','Perl CGI::Session'),
            ('GX_SESSION_ID','GeneXus'),
            ('WC_SESSION_ESTABLISHED','WSStore'),

        )

    def __init__(self):
        GrepPlugin.__init__(self)
        self._already_reported_server = []

    def grep(self, request, response):
        '''
        Plugin entry point, search for cookies.
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        headers = response.getHeaders()
        
        for header_name in headers:  
            if header_name.lower() in self.COOKIE_HEADERS:

                # Create the object to save the cookie in the kb
                i = info.info()
                i.setPluginName(self.getName())
                i.setName('Cookie')
                i.setURL( response.getURL() )

                self._set_cookie_to_rep(i, cstr=headers[header_name].strip())
                 
                cookie_object = Cookie.SimpleCookie()
                try:
                    # Note to self: This line may print some chars to the console
                    cookie_object.load( headers[ header_name ].strip() )
                except Cookie.CookieError:
                    # The cookie is invalid, this is worth mentioning ;)
                    msg = 'The cookie that was sent by the remote web application'
                    msg += ' does NOT respect the RFC.'
                    om.out.information(msg)
                    i.setDesc(msg)
                    i.setName('Invalid cookie')
                    kb.kb.append( self, 'invalid-cookies', i )
                else:
                    
                    for cookie_info in kb.kb.getData( self, 'cookies' ):
                        stored_cookie_obj = cookie_info['cookie-object']
                        if cookie_object == stored_cookie_obj:
                            break
                    else:
                        i['cookie-object'] = cookie_object
    
                        '''
                        The expiration date tells the browser when to delete the cookie. If no 
                        expiration date is provided, the cookie is deleted at the end of the user
                        session, that is, when the user quits the browser. As a result, specifying an
                        expiration date is a means for making cookies to survive across browser 
                        sessions. For this reason, cookies that have an expiration date are called 
                        persistent.
                        '''
                        i['persistent'] = False
                        if 'expires' in cookie_object:
                            i['persistent'] = True
                            
                        i.setId( response.id )
                        i.addToHighlight(i['cookie-string'])
                        msg = 'The URL: "' + i.getURL() + '" sent the cookie: "'
                        msg += i['cookie-string'] + '".'
                        i.setDesc( msg )
                        kb.kb.append( self, 'cookies', i )
                        
                        # Find if the cookie introduces any vulnerability, or discloses information
                        self._analyze_cookie( request, response, cookie_object )
        
        # do this check every time
        self._sslCookieValueUsedInHTTP( request, response )
    
    def _analyze_cookie( self, request, response, cookieObj ):
        '''
        In this method I call all the other methods that perform a specific
        analysis of the already catched cookie.
        '''
        self._match_cookie_fingerprint( request, response, cookieObj )
        self._secure_over_http( request, response, cookieObj )
        self._http_only( request, response, cookieObj )
        
    def _http_only(self, request, response, cookieObj ):
        '''
        Verify if the cookie has the httpOnly parameter set
        
        Reference:
            http://www.owasp.org/index.php/HTTPOnly
            http://en.wikipedia.org/wiki/HTTP_cookie
        
        @parameter request: The http request object
        @parameter response: The http response object
        @parameter cookieObj: The cookie object to analyze
        @return: None
        '''
        ### TODO: Code this!
        pass
            
    def _sslCookieValueUsedInHTTP( self, request, response ):
        '''
        Analyze if a cookie value, sent in a HTTPS request, is now used for 
        identifying the user in an insecure page. Example:
            Login is done over SSL
            The rest of the page is HTTP
        '''
        if request.getURL().getProtocol().lower() == 'http':
            for cookie in kb.kb.getData( 'collect_cookies', 'cookies' ):
                if cookie.getURL().getProtocol().lower() == 'https' and \
                request.getURL().getDomain() == cookie.getURL().getDomain():
                    # The cookie was sent using SSL, I'll check if the current 
                    # request, is using this values in the POSTDATA / QS / COOKIE
                    for key in cookie['cookie-object'].keys():
                        # This if is to create less false positives
                        if len( cookie['cookie-object'][key] ) > 4:
                            
                            for parameter_name in request.getDc():
                                
                                # added to support repeated parameter names.
                                for parameter_value_i in request.getDc()[parameter_name]:
                                    
                                    # The first statement of this if is to make this algorithm faster
                                    if len( parameter_value_i ) > 4 and parameter_value_i == cookie['cookie-object'][key]:
                                        v = vuln.vuln()
                                        v.setPluginName(self.getName())
                                        v.setURL( response.getURL() )
                                        self._set_cookie_to_rep(v, cobj=cookie)
                                        v.setSeverity(severity.HIGH)
                                        v.setId( response.id )
                                        v.setName( 'Secure cookies over insecure channel' )
                                        msg = 'Cookie values that were set over HTTPS, are sent over '
                                        msg += 'an insecure channel when requesting URL: "' 
                                        msg += request.getURL() + '" , parameter "' + parameter_name + '"'
                                        v.setDesc( msg )
                                        kb.kb.append( self, 'cookies', v )
            
    def _match_cookie_fingerprint( self, request, response, cookieObj ):
        '''
        Now we analize and try to guess the remote web server based on the
        cookie that was sent.
        '''
        for cookie in self.COOKIE_FINGERPRINT:
            if cookie[0] in cookieObj.output(header=''):
                if cookie[1] not in self._already_reported_server:
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setId( response.id )
                    i.setName('Identified cookie')
                    i.setURL( response.getURL() )
                    self._set_cookie_to_rep(i, cobj=cookieObj)
                    i['httpd'] = cookie[1]
                    i.setDesc( 'A cookie matching the cookie fingerprint DB ' +
                    'has been found when requesting "' + response.getURL() + '" . ' +
                    'The remote platform is: "' + cookie[1] + '"')
                    kb.kb.append( self, 'cookies', i )
                    self._already_reported_server.append( cookie[1] )

    def _secure_over_http( self, request, response, cookieObj ):
        '''
        Checks if a cookie marked as secure is sent over http.
        
        Reference:
            http://en.wikipedia.org/wiki/HTTP_cookie
        
        @parameter request: The http request object
        @parameter response: The http response object
        @parameter cookieObj: The cookie object to analyze
        @return: None
        '''
        ### BUGBUG: There is a bug in python cookie.py which makes this
        ### code useless! The secure parameter is never parsed in the cookieObj
        ### http://bugs.python.org/issue1028088
        ### https://sourceforge.net/tracker2/?func=detail&aid=2139517&group_id=170274&atid=853655
        if 'secure' in cookieObj and response.getURL().getProtocol().lower() == 'http':
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setURL( response.getURL() )
            v.setId( response.getId() )
            self._set_cookie_to_rep(v, cobj=cookieObj)
            v.setSeverity(severity.HIGH)
            v.setName( 'Secure cookies over insecure channel' )
            msg = 'A cookie marked as secure was sent over an insecure channel'
            msg += ' when requesting the URL: "' + response.getURL() + '"'
            v.setDesc( msg )
            kb.kb.append( self, 'cookies', v )
        
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        cookies = kb.kb.getData( 'collect_cookies', 'cookies' )
            
        # Group correctly
        tmp = []
        for c in cookies:
            tmp.append( (c['cookie-string'], c.getURL() ) )
        
        # And don't print duplicates
        tmp = list(set(tmp))
        
        resDict, itemIndex = groupbyMinKey( tmp )
        if itemIndex == 0:
            # Grouped by cookies
            msg = 'The cookie: "%s" was sent by these URLs:'
        else:
            # Grouped by URLs
            msg = 'The URL: "%s" sent these cookies:'
            
        for k in resDict:
            om.out.information(msg % k)
            for i in resDict[k]:
                om.out.information('- ' + i )

    def _set_cookie_to_rep(self, inst, cobj=None, cstr=None):
        if cobj is not None:
            obj = cobj
            inst['cookie-object'] = obj
            cstr = obj.output(header='')
        
        if cstr is not None:
            inst['cookie-string'] = cstr
        
            if cstr:
                inst.addToHighlight(cstr)
    
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every response for session cookies that the web 
        application sends to the client, and analyzes them in order to identify
        potential vulnerabilities, the remote web application framework and
        other interesting information.
        '''
