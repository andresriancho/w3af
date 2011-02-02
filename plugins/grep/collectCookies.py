'''
collectCookies.py

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

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

import Cookie

import core.data.parsers.urlParser as urlParser
from core.controllers.misc.groupbyMinKey import groupbyMinKey


class collectCookies(baseGrepPlugin):
    '''
    Grep every response for session cookies sent by the web application.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._already_reported_server = []
        self._cookieHeaders = ['Set-Cookie'.upper(), 'Cookie'.upper(), 'Cookie2'.upper()]

    def _setCookieToRep(self, inst, **kwd):
        if 'cobj' in kwd:
            obj = kwd['cobj']
            inst['cookie-object'] = obj
            cstr = obj.output(header='')
        elif 'cstr' in kwd:
            cstr = kwd['cstr']
            
        if cstr:
            inst['cookie-string'] = cstr
            inst.addToHighlight(cstr)
    
    def grep(self, request, response):
        '''
        Plugin entry point, search for cookies.
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        for key in response.getHeaders():  
            if key.upper() in self._cookieHeaders:
                # save
                headers = response.getHeaders()
                
                # Create the object to save the cookie in the kb
                i = info.info()
                i.setPluginName(self.getName())
                i.setName('Cookie')
                i.setURL( response.getURL() )
                cookieStr = headers[key].strip()
                self._setCookieToRep(i, cstr=headers[key].strip())
                 
                C = Cookie.SimpleCookie()
                try:
                    # Note to self: This line may print some chars to the console
                    C.load( headers[ key ].strip() )
                except Cookie.CookieError:
                    # The cookie is invalid, this is worth mentioning ;)
                    msg = 'The cookie that was sent by the remote web application'
                    msg += ' doesn\'t respect the RFC.'
                    om.out.information(msg)
                    i.setDesc(msg)
                    i.setName('Invalid cookie')
                    kb.kb.append( self, 'invalid-cookies', i )
                else:
                    i['cookie-object'] = C

                    '''
                    The expiration date tells the browser when to delete the cookie. If no 
                    expiration date is provided, the cookie is deleted at the end of the user
                    session, that is, when the user quits the browser. As a result, specifying an
                    expiration date is a means for making cookies to survive across browser 
                    sessions. For this reason, cookies that have an expiration date are called 
                    persistent.
                    '''
                    i['persistent'] = False
                    if 'expires' in C:
                        i['persistent'] = True
                        
                    i.setId( response.id )
                    i.addToHighlight(i['cookie-string'])
                    msg = 'The URL: "' + i.getURL() + '" sent the cookie: "'
                    msg += i['cookie-string'] + '".'
                    i.setDesc( msg )
                    kb.kb.append( self, 'cookies', i )
                    
                    # Find if the cookie introduces any vulnerability, or discloses information
                    self._analyzeCookie( request, response, C )
        
        # do this check everytime
        self._sslCookieValueUsedInHTTP( request, response )
    
    def _analyzeCookie( self, request, response, cookieObj ):
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
        Analyze if a cookie value, sent in a HTTPS request, is now used for identifying the user in an insecure page.
        Example:
            Login is done over SSL
            The rest of the page is HTTP
        '''
        if request.getURL().startswith('http://'):
            for cookie in kb.kb.getData( 'collectCookies', 'cookies' ):
                if cookie.getURL().startswith('https://') and \
                urlParser.getDomain( request.getURL() ) == urlParser.getDomain( cookie.getURL() ):
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
                                        self._setCookieToRep(v, cobj=cookie)
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
        for cookie in self._get_fingerprint_db():
            if cookie[0] in cookieObj.output(header=''):
                if cookie[1] not in self._already_reported_server:
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setId( response.id )
                    i.setName('Identified cookie')
                    i.setURL( response.getURL() )
                    self._setCookieToRep(i, cobj=cookieObj)
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
        if 'secure' in cookieObj and response.getURL().startswith('http://'):
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setURL( response.getURL() )
            v.setId( response.getId() )
            self._setCookieToRep(v, cobj=cookieObj)
            v.setSeverity(severity.HIGH)
            v.setName( 'Secure cookies over insecure channel' )
            msg = 'A cookie marked as secure was sent over an insecure channel'
            msg += ' when requesting the URL: "' + response.getURL() + '"'
            v.setDesc( msg )
            kb.kb.append( self, 'cookies', v )
        
    def _get_fingerprint_db(self):
        '''
        @return: A list of tuples with ( CookieString, WebServerType )
        '''
        # This is a simplificated version of ramon's cookie db.
        cookie_db = []
        
        # Web application firewalls
        cookie_db.append( ('st8id=','Teros web application firewall') )
        cookie_db.append( ('ASINFO=','F5 TrafficShield') )
        cookie_db.append( ('NCI__SessionId=','Netcontinuum') )
        
        # oracle
        cookie_db.append( ('$OC4J_','Oracle container for java') )
        
        # Java
        cookie_db.append( ('JSESSIONID=','Jakarta Tomcat / Apache') )
        cookie_db.append( ('JServSessionIdroot=','Apache JServ') )
        
        # ASP
        cookie_db.append( ('ASPSESSIONID','ASP') )
        cookie_db.append( ('ASP.NET_SessionId=','ASP.NET') )
        cookie_db.append( ('cadata=; path=/; expires=Thu, 01-Jan-1970 00:00:00 GMT',
                                        'Outlook Web Access') )
        
        # PHP
        cookie_db.append( ('PHPSESSID=','PHP') )
        
        # SAP
        cookie_db.append( ('sap-usercontext=sap-language=','SAP') )
        
        # Others
        cookie_db.append( ('WebLogicSession=','BEA Logic') )
        cookie_db.append( ('SaneID=','Sane NetTracker') )
        cookie_db.append( ('ssuid=','Vignette') )
        cookie_db.append( ('vgnvisitor=','Vignette') )
        cookie_db.append( ('SESSION_ID=','IBM Net.Commerce') )
        cookie_db.append( ('NSES40Session=','Netscape Enterprise Server') )
        cookie_db.append( ('iPlanetUserId=','iPlanet') )
        cookie_db.append( ('RMID=','RealMedia OpenADStream') )
        cookie_db.append( ('cftoken=','Coldfusion') )
        cookie_db.append( ('PORTAL-PSJSESSIONID=','PeopleSoft') )
        cookie_db.append( ('WEBTRENDS_ID=','WebTrends') )
        cookie_db.append( ('sesessionid=','IBM WebSphere') )
        cookie_db.append( ('CGISESSID=','Perl CGI::Session') )
        cookie_db.append( ('GX_SESSION_ID','GeneXus') )
        cookie_db.append( ('WC_SESSION_ESTABLISHED','WSStore') )
        
        return cookie_db
        
    def setOptions( self, OptionList ):
        pass
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        cookies = kb.kb.getData( 'collectCookies', 'cookies' )
            
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
        This plugin greps every response for session cookies that the web application sends
        to the client, and analyzes them in order to identify potential vulnerabilities, the
        remote web application framework and other interesting information.
        '''
