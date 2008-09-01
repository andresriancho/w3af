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

import core.data.parsers.htmlParser as htmlParser
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import Cookie
import core.data.parsers.urlParser as urlParser
import core.data.kb.vuln as vuln
from core.controllers.misc.groupbyMinKey import groupbyMinKey
import core.data.constants.severity as severity

class collectCookies(baseGrepPlugin):
    '''
    Grep every response for session cookies sent by the web application.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._alreadyReportedServer = []
        self._cookieHeaders = ['Set-Cookie'.upper(),'Cookie'.upper(),'Cookie2'.upper()]
    
    def _testResponse(self, request, response):
        
        for key in response.getHeaders():  
            if key.upper() in self._cookieHeaders:
                # save
                headers = response.getHeaders()
                
                # Load the cookie in the kb
                i = info.info()
                i.setName('Cookie')
                i.setURL( response.getURL() )
                i['cookie-string'] = headers[key].strip()
                
                C = Cookie.SimpleCookie()
                C.load( headers[ key ].strip() )
                i['cookie-object'] = C
                
                '''
                The expiration date tells the browser when to delete the cookie. If no expiration date is provided, the cookie is 
                deleted at the end of the user session, that is, when the user quits the browser. As a result, specifying an expiration 
                date is a means for making cookies to survive across browser sessions. For this reason, cookies that have an expiration
                date are called persistent.
                '''
                i['persistent'] = False
                if 'expires' in C:
                    i['persistent'] = True
                    
                i.setId( response.id )
                i.setDesc( 'The URL: "' + i.getURL() + '" sent the cookie: ' + i['cookie-string'] )
                kb.kb.append( self, 'cookies', i )
                
                # Find if the cookie introduces any vulnerability, or discloses information
                self._analyzeCookie( request, response, C )
        
        # do this check everytime
        self._sslCookieValueUsedInHTTP( request, response )
    
    def _analyzeCookie( self, request, response, cookieObj ):
        self._identifyServer( request, response, cookieObj )
        self._secureOverHTTP( request, response, cookieObj )
        
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
                            for item in request.getDc().items():
                                # The first statement of this if is to make this algorithm faster
                                if len( item[1] ) > 4 and item[1] == cookie['cookie-object'][key]:
                                    v = vuln.vuln()
                                    v.setURL( response.getURL() )
                                    v['cookie-string'] = cookie.output(header='')
                                    v['cookie-object'] = cookie
                                    v.setSeverity(severity.HIGH)
                                    v.setId( response.id )
                                    v.setName( 'Secure cookies over insecure channel' )                                    
                                    v.setDesc( 'Cookie values that were set over HTTPS, are sent over an insecure channel when requesting URL: ' + request.getURL() + ' , parameter ' + item[0] )
                                    kb.kb.append( self, 'cookies', v )
            
    def _identifyServer( self, request, response, cookieObj ):
        '''
        Now we analize and try to guess the remote web server based on the
        cookie that was sent.
        '''
        for cookie in self._getCookieFPdb():
            if cookie[0] in cookieObj.output(header=''):
                if cookie[1] not in self._alreadyReportedServer:
                    i = info.info()
                    i.setId( response.id )
                    i.setName('Identified cookie')
                    i.setURL( response.getURL() )
                    i['cookie-string'] = cookieObj.output(header='')
                    i['cookie-object'] = cookieObj
                    i['httpd'] = cookie[1]
                    i.setDesc( 'A cookie matching the cookie fingerprint DB ' +
                    'has been found when requesting ' + response.getURL() + ' . The remote platform is: ' + cookie[1] )
                    kb.kb.append( self, 'cookies', i )
                    self._alreadyReportedServer.append( cookie[1] )

    def _secureOverHTTP( self, request, response, cookieObj ):
        '''
        Checks if a cookie marked as secure is sent over http.
        '''
        if 'secure' in cookieObj and response.getURL().startswith('http://'):
            v = vuln.vuln()
            v.setURL( response.getURL() )
            v.setId( response.getId() )
            v['cookie-string'] = cookieObj.output(header='')
            v['cookie-object'] = cookieObj
            v.setSeverity(severity.HIGH)
            v.setName( 'Secure cookies over insecure channel' )                  
            v.setDesc( 'A cookie marked as secure was sent over an insecure channel when requesting the URL: ' + response.getURL() )
            kb.kb.append( self, 'cookies', v )
        
    def _getCookieFPdb(self):
        '''
        @return: A list of tuples with ( CookieString, WebServerType )
        '''
        # This is a simplificated version of ramon's cookie db.
        cookieDB = []
        
        # Web application firewalls
        cookieDB.append( ('st8id=','Teros web application firewall') )
        cookieDB.append( ('ASINFO=','F5 TrafficShield') )
        cookieDB.append( ('NCI__SessionId=','Netcontinuum') )
        
        # oracle
        cookieDB.append( ('$OC4J_','Oracle container for java') )
        
        # Java
        cookieDB.append( ('JSESSIONID=','Jakarta Tomcat / Apache') )
        cookieDB.append( ('JServSessionIdroot=','Apache JServ') )
        
        # ASP
        cookieDB.append( ('ASPSESSIONID','ASP') )
        
        # PHP
        cookieDB.append( ('PHPSESSID=','PHP') )
        
        # Others
        cookieDB.append( ('WebLogicSession=','BEA Logic') )
        cookieDB.append( ('SaneID=','Sane NetTracker') )
        cookieDB.append( ('ssuid=','Vignette') )
        cookieDB.append( ('vgnvisitor=','Vignette') )
        cookieDB.append( ('SESSION_ID=','IBM Net.Commerce') )
        cookieDB.append( ('NSES40Session=','Netscape Enterprise Server') )
        cookieDB.append( ('iPlanetUserId=','iPlanet') )
        cookieDB.append( ('RMID=','RealMedia OpenADStream') )
        cookieDB.append( ('cftoken=','Coldfusion') )
        cookieDB.append( ('PORTAL-PSJSESSIONID=','PeopleSoft') )
        cookieDB.append( ('WEBTRENDS_ID=','WebTrends') )
        cookieDB.append( ('sesessionid=','IBM WebSphere') )
        cookieDB.append( ('CGISESSID=','Perl CGI::Session') )
        cookieDB.append( ('GX_SESSION_ID','GeneXus') )
        cookieDB.append( ('WC_SESSION_ESTABLISHED','WSStore') )
        
        return cookieDB
        
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
        This plugin greps every response for session cookies that the web app sends to the client.
        '''
