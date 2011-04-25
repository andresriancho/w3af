'''
baseAttackPlugin.py

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

from core.controllers.w3afException import w3afException
from core.controllers.basePlugin.basePlugin import basePlugin
import core.controllers.outputManager as om
import core.data.request.httpPostDataRequest as httpPostDataRequest
import copy
import core.data.kb.knowledgeBase as kb
from core.controllers.misc.commonAttackMethods import commonAttackMethods

class baseAttackPlugin(basePlugin, commonAttackMethods):
    '''
    This is the base class for attack plugins, all attack plugins should inherit from it 
    and implement the following methods :
        1. fastExploit(...)
        2. _generateShell(...)
        
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        basePlugin.__init__( self )
        commonAttackMethods.__init__( self )
        
        self._urlOpener = None
        self._footer = None
        self._header = None
        
        # User configured parameter
        self._generateOnlyOne = False

    def fastExploit(self, url ):
        '''
        '''
        raise w3afException('Plugin is not implementing required method fastExploit' )
        
    def _generateShell( self, vuln ):
        '''
        @parameter vuln: The vulnerability object to exploit.
        '''
        raise w3afException('Plugin is not implementing required method _generateShell' )
        
    def getExploitableVulns(self):
        return kb.kb.getData( self.getVulnName2Exploit() , self.getVulnName2Exploit() )
        
    def canExploit(self, vulnToExploit=None):
        '''
        Determines if audit plugins found exploitable vulns.
        
        @parameter vulnToExploit: The vulnerability id to exploit
        @return: True if we can exploit a vuln stored in the kb.
        '''
        vulns = self.getExploitableVulns()
        if vulnToExploit is not None:
            vulns = [ v for v in vulns if v.getId() == vulnToExploit ]
            if vulns:
                return True
            else:
                return False
        else:
            # The user didn't specified what vuln to exploit... so...
            if vulns:
                return True
            else:
                return False

    def getAttackType(self):
        '''
        @return: The type of exploit, SHELL, PROXY, etc.
        '''
        raise w3afException('Plugin is not implementing required method getAttackType' )

    def GET2POST( self, vuln ):
        '''
        This method changes a vulnerability mutant, so all the data that was sent in the query string,
        is now sent in the postData; of course, the HTTP method is also changed from GET to POST.
        '''
        vulnCopy = copy.deepcopy( vuln )
        mutant = vulnCopy.getMutant()
        
        #    Sometimes there is no mutant (php_sca).
        if mutant is None:
            return vulnCopy
        
        if mutant.getMethod() == 'POST':
            # No need to work !
            return vulnCopy
            
        else:
            pdr = httpPostDataRequest.httpPostDataRequest()
            pdr.setURL( mutant.getURL() )
            pdr.setDc( mutant.getDc() )
            pdr.setHeaders( mutant.getHeaders() )
            pdr.setCookie( mutant.getCookie() )
            mutant.setFuzzableReq( pdr )
            return vulnCopy
            
    def getRootProbability( self ):
        '''
        @return: This method returns the probability of getting a root shell using this attack plugin.
        This is used by the "exploit *" function to order the plugins and first try to exploit the more critical ones.
        This method should return 0 for an exploit that will never return a root shell, and 1 for an exploit that WILL ALWAYS
        return a root shell.
        '''
        raise w3afException( 'Plugin is not implementing required method getRootProbability' )
        
    def getType( self ):
        return 'attack'
        
    def getVulnName2Exploit( self ):
        '''
        This method should return the vulnerability name (as saved in the kb) to exploit.
        For example, if the audit.osCommanding plugin finds an vuln, and saves it as:
        
        kb.kb.append( 'osCommanding' , 'osCommanding', vuln )
        
        Then the exploit plugin that exploits osCommanding ( attack.osCommandingShell ) should
        return 'osCommanding' in this method.
        '''
        raise w3afException( 'Plugin is not implementing required method getVulnName2Exploit' )
    
    def exploit( self, vulnToExploit=None):
        '''
        Exploits a vuln that was found and stored in the kb.
        
        @parameter vulnToExploit: The vulnerability id to exploit
        @return: A list of shells of proxies generated by the exploitation phase
        '''
        om.out.information( self.getName() + ' exploit plugin is starting.' )
        if not self.canExploit():
            raise w3afException('No '+ self.getVulnName2Exploit() + ' vulnerabilities have been found.')

        for vuln in self.getExploitableVulns():
            
            if vulnToExploit is not None:
                if vulnToExploit != vuln.getId():
                    continue
                    
            # Try to get a shell using a vuln
            s = self._generateShell(vuln)
            if s is not None:
                kb.kb.append( self, 'shell', s )
                if self._generateOnlyOne:
                    # A shell was generated, I only need one point of exec.
                    return [s,]
                else:
                    # Keep adding all shells to the kb
                    # this is done 5 lines before this comment
                    pass
        
        return kb.kb.getData( self.getName(), 'shell' )
