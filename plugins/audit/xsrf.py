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

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.controllers.w3afException import w3afException
from core.data.exchangableMethods import isExchangable
from core.data.parsers.urlParser import hasQueryString

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
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
        
        # Internal variables
        self._vuln_simple = []
        self._vuln_complex = []
        self._already_reported = False

    def audit(self, freq ):
        '''
        Tests an URL for xsrf vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'xsrf plugin is testing: ' + freq.getURL() )

        # Vulnerable by definition
        if freq.getMethod() == 'GET' and hasQueryString( freq.getURI() ):
            
            # Now check if we already added this target URL to the list
            already_added = [ v.getURL() for v in self._vuln_simple ]
            if freq.getURL() not in already_added:
                
                # Vulnerable and not in list, add:
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setURL( freq.getURL() )
                v.setDc( freq.getDc() )
                v.setName( 'Cross site request forgery vulnerability' )
                v.setSeverity(severity.LOW)
                v.setMethod( freq.getMethod() )
                v.setDesc( 'The URL: ' + freq.getURL() + ' is vulnerable to cross site request forgery.' )
                self._vuln_simple.append( v )
        
        # This is a POST request that can be sent using a GET and querystring
        # Vulnerable by definition
        elif freq.getMethod() =='POST' and len ( freq.getDc() ) and isExchangable( self, freq ):
            
            # Now check if we already added this target URL to the list
            already_added = [ v.getURL() for v in self._vuln_complex ]
            if freq.getURL() not in already_added:
                
                # Vulnerable and not in list, add:
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setURL( freq.getURL() )
                v.setSeverity(severity.LOW)
                v.setDc( freq.getDc() )
                v.setName( 'Cross site request forgery vulnerability' )
                v.setMethod( freq.getMethod() )
                msg = 'The URL: ' + freq.getURL() + ' is vulnerable to cross site request forgery.'
                msg += ' It allows the attacker to exchange the method from POST to GET when sending'
                msg += ' data to the server.'
                v.setDesc( msg )
                self._vuln_complex.append( v )
    
    def end( self ):
        '''
        This method is called at the end, when w3afCore aint going to use this plugin anymore.
        '''
        has_persistent_cookie = False
        cookies = kb.kb.getData( 'collectCookies', 'cookies' )
        for cookie in cookies:
            if cookie.has_key('persistent'):
                if not self._already_reported:
                    om.out.information('The web application sent a persistent cookie.')
                    has_persistent_cookie = True
                    self._already_reported = True
                    break
        
        # If there is at least one persistent cookie
        if has_persistent_cookie:
            if len( self._vuln_simple ):
                om.out.vulnerability('The following scripts are vulnerable to a trivial form of XSRF:',
                        severity=severity.LOW)
                
                fr_str = list(set([ str(v.getURL()) for v in self._vuln_simple ]))
                kb.kb.save( self, 'get_xsrf', self._vuln_simple )
                
                for i in fr_str:
                    om.out.vulnerability( '- ' + i, severity=severity.LOW )
            
            if len( self._vuln_complex ):
                msg = 'The following scripts allow an attacker to send POST data as query string'
                msg +=' data (this makes XSRF easier to exploit):'
                om.out.vulnerability(msg, severity=severity.LOW)
                
                fr_str = list(set([ str(fr) for fr in self._vuln_complex ]))
                kb.kb.save( self, 'post_xsrf', self._vuln_complex )
                
                for i in fr_str:
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
        This plugin finds Cross Site Request Forgeries (XSRF) vulnerabilities.
        
        The simplest type of XSRF is checked, to be vulnerable, the web application must have sent a permanent
        cookie, and the aplicacion must have query string parameters.
        '''
