'''
xsrf.py

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

import core.data.kb.vuln as vuln
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
import core.data.kb.knowledgeBase as kb
from core.controllers.w3afException import w3afException
from core.data.exchangableMethods import *
from core.data.parsers.urlParser import hasQueryString
import core.data.constants.severity as severity

class xsrf(baseAuditPlugin):
    '''
    Find the easiest to exploit xsrf vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    '''
    By easiest i mean, someone sending a victim a link like this one:
        https://bank.com/homeBanking/transferMoney.aspx?amount=1000&dstAccount=attackerAccount
    
    AND the web application at bank.com sends a cookie that is persistent.
    
    Note: I do realize that xsrf can be exploited using javascript to do POSTS's impersonating the user.
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        self._vulnSimple = []
        self._vulnComplex = []
        self._alreadyReported = False

    def _fuzzRequests(self, freq ):
        '''
        Tests an URL for xsrf vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'xsrf plugin is testing: ' + freq.getURL() )

        if freq.getMethod() == 'GET' and hasQueryString( freq.getURI() ):
            # Vulnerable by definition
            v = vuln.vuln()
            v.setURL( freq.getURL() )
            v.setDc( freq.getDc() )
            v.setName( 'Cross site request forgery vulnerability' )
            v.setSeverity(severity.LOW)
            v.setMethod( freq.getMethod() )
            v.setDesc( 'The URL: ' + freq.getURL() + ' is vulnerable to cross site request forgery.' )
            v.setId( 0 )
            self._vulnSimple.append( v )
        
        elif freq.getMethod() =='POST' and len ( freq.getDc() ) and isExchangable( self, freq ):
            # This is a POST request that can be sent using a GET and querystring
            # Vulnerable by definition
            v = vuln.vuln()
            v.setURL( freq.getURL() )
            v.setSeverity(severity.LOW)
            v.setDc( freq.getDc() )
            v.setName( 'Cross site request forgery vulnerability' )
            v.setMethod( freq.getMethod() )         
            v.setDesc( 'The URL: ' + freq.getURL() + ' is vulnerable to cross site request forgery. It allows the attacker to exchange the method from POST to GET when sending data to the server.' )
            v.setId( 0 )
            self._vulnComplex.append( v )
    
    def end( self ):
        '''
        This method is called at the end, when w3afCore aint going to use this plugin anymore.
        '''
        hasPersistentCookie = False
        cookies = kb.kb.getData( 'collectCookies', 'cookies' )
        for cookie in cookies:
            if cookie.has_key('persistent'):
                if not self._alreadyReported:
                    om.out.information('The web application sent a persistent cookie.')
                    hasPersistentCookie = True
                    self._alreadyReported = True
        
        # If there is at least one persistent cookie
        if hasPersistentCookie:
            if len( self._vulnSimple ):
                om.out.vulnerability('The following scripts are vulnerable to a trivial form of XSRF:', severity=severity.LOW)
                
                frStr = list(set([ str(v.getURL()) for v in self._vulnSimple ]))
                kb.kb.save( self, 'get_xsrf', self._vulnSimple )
                
                for i in frStr:
                    om.out.vulnerability( '- ' + i, severity=severity.LOW )
            
            if len( self._vulnComplex ):
                om.out.vulnerability('The following scripts allow an attacker to send POST data as query string data (this makes XSRF more easy to exploit):', severity=severity.LOW)            
                frStr = list(set([ str(fr) for fr in self._vulnComplex ]))
                kb.kb.save( self, 'post_xsrf', self._vulnComplex )
                
                for i in frStr:
                    om.out.vulnerability( '- ' + i, severity=severity.LOW )
                
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return ['grep.collectCookies']

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin will find Cross Site Request Forgeries (XSRF) vulnerabilities on the web application.
        The simplest type of XSRF is checked, to be vulnerable, the web application must have sent a permanent
        cookie, and the aplicacion must have query string parameters.
        '''
