'''
fingerprint_WAF.py

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

from core.data.fuzzer.fuzzer import createRandAlpha
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.w3afException import w3afException
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.w3afException import w3afRunOnce
import re

class fingerprint_WAF(baseDiscoveryPlugin):
    '''
    Identify if a Web Application Firewall is present and if possible identify the vendor and version.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._run = True
        
    def discover(self, fuzzableRequest ):
        '''
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        if not self._run:
            # This will remove the plugin from the discovery plugins 
            # to be runned.
            raise w3afRunOnce()
        else:
            # I will only run this one time. All calls to fingerprint_WAF return 
            # the same url's ( none! )
            self._run = False
            self._fingerprint_URLScan( fuzzableRequest )
            self._fingerprint_ModSecurity( fuzzableRequest )
            self._fingerprint_SecureIIS( fuzzableRequest )
            self._fingerprint_Airlock( fuzzableRequest )
            self._fingerprint_Barracuda( fuzzableRequest )
            self._fingerprint_DenyAll( fuzzableRequest )
            self._fingerprint_F5ASM( fuzzableRequest )
            self._fingerprint_HyperGuard( fuzzableRequest )

        return []
    
    def _fingerprint_SecureIIS(self,  fuzzableRequest):
        '''
        Try to verify if SecureIIS is installed or not.
        '''
        # And now a final check for SecureIIS
        headers = fuzzableRequest.getHeaders()
        headers['Transfer-Encoding'] = createRandAlpha(1024 + 1)
        try:
            lockResponse2 = self._urlOpener.GET( fuzzableRequest.getURL(), headers=headers, useCache=True )
        except w3afException, w3:
            om.out.debug('Failed to identify secure IIS, exception: ' + str(w3) )
        else:
            if lockResponse2.getCode() == 404:
                self._reportFinding('SecureIIS', lockResponse2)
        
    def _fingerprint_ModSecurity(self,  fuzzableRequest):
        '''
        Try to verify if mod_security is installed or not AND try to get the installed version.
        '''
        pass

    def _fingerprint_Airlock(self,  fuzzableRequest):
        '''
        Try to verify if Airlock is present.
        '''
        om.out.debug( 'detect Airlock' )
        try:
            response = self._urlOpener.GET( fuzzableRequest.getURL(), useCache=True )
        except KeyboardInterrupt,e:
            raise e
        else:
            for h in response.getHeaders().keys():
                if h.lower() == 'set-cookie':
                    protectedBy = response.getHeaders()[h]
                    if re.match('^AL[_-]?(SESS|LB)=', protectedBy):
                        om.out.information( 'URL protected: ' + protectedBy )
                        self._reportFinding('Airlock', response)
                        return
                # else 
                    # more checks, like path /error_path or encrypted URL in response

    def _fingerprint_Barracuda(self,  fuzzableRequest):
        '''
        Try to verify if Barracuda is present.
        '''
        om.out.debug( 'detect Barracuda' )
        try:
            response = self._urlOpener.GET( fuzzableRequest.getURL(), useCache=True )
        except KeyboardInterrupt,e:
            raise e
        else:
            for h in response.getHeaders().keys():
                if h.lower() == 'set-cookie':
                    # ToDo: not sure if this is always there (08jul08 Achim)
                    protectedBy = response.getHeaders()[h]
                    if re.match('^barra_counter_session=', protectedBy):
                        om.out.information( 'URL protected: ' + protectedBy )
                        self._reportFinding('Barracuda', response)
                        return
                # else 
                    # don't know ...

    def _fingerprint_DenyAll(self,  fuzzableRequest):
        '''
        Try to verify if Deny All rWeb is present.
        '''
        om.out.debug( 'detect Deny All' )
        try:
            response = self._urlOpener.GET( fuzzableRequest.getURL(), useCache=True )
        except KeyboardInterrupt,e:
            raise e
        else:
            for h in response.getHeaders().keys():
                if h.lower() == 'set-cookie':
                    protectedBy = response.getHeaders()[h]
                    if re.match('^sessioncookie=', protectedBy):
                        om.out.information( 'URL protected: ' + protectedBy )
                        self._reportFinding('Deny All rWeb', response)
                        return
                # else
                    # more checks like detection=detected cookie

    def _fingerprint_F5ASM(self,  fuzzableRequest):
        '''
        Try to verify if F5 ASM (also TrafficShield) is present.
        '''
        om.out.debug( 'detect F5 ASM or TrafficShield' )
        try:
            response = self._urlOpener.GET( fuzzableRequest.getURL(), useCache=True )
        except KeyboardInterrupt,e:
            raise e
        else:
            for h in response.getHeaders().keys():
                if h.lower() == 'set-cookie':
                    protectedBy = response.getHeaders()[h]
                    if re.match('^TS[a-zA-Z0-9]{3,6}=', protectedBy):
                        om.out.information( 'URL protected: ' + protectedBy )
                        self._reportFinding('F5 ASM', response)
                        return
                # else
                    # more checks like special string in response

    def _fingerprint_HyperGuard(self,  fuzzableRequest):
        '''
        Try to verify if HyperGuard is present.
        '''
        om.out.debug( 'detect HyperGuard' )
        try:
            response = self._urlOpener.GET( fuzzableRequest.getURL(), useCache=True )
        except KeyboardInterrupt,e:
            raise e
        else:
            for h in response.getHeaders().keys():
                if h.lower() == 'set-cookie':
                    protectedBy = response.getHeaders()[h]
                    if re.match('^WODSESSION=', protectedBy):
                        om.out.information( 'URL protected: ' + protectedBy )
                        self._reportFinding('HyperGuard', response)
                        return
                # else
                    # more checks like special string in response

    def _fingerprint_URLScan(self,  fuzzableRequest):
        '''
        Try to verify if URLScan is installed or not.
        '''
        # detect using GET
        # Get the original response
        originalResponse = self._urlOpener.GET( fuzzableRequest.getURL(), useCache=True )
        if originalResponse.getCode() != 404:
            # Now add the if header and try again
            headers = fuzzableRequest.getHeaders()
            headers['If'] = createRandAlpha(8)
            ifResponse = self._urlOpener.GET( fuzzableRequest.getURL(), headers=headers, useCache=True )
            
            headers = fuzzableRequest.getHeaders()
            headers['Translate'] = createRandAlpha(8)
            translateResponse = self._urlOpener.GET( fuzzableRequest.getURL(), headers=headers, useCache=True )
            
            headers = fuzzableRequest.getHeaders()
            headers['Lock-Token'] = createRandAlpha(8)
            lockResponse = self._urlOpener.GET( fuzzableRequest.getURL(), headers=headers, useCache=True )
            
            headers = fuzzableRequest.getHeaders()
            headers['Transfer-Encoding'] = createRandAlpha(8)
            transferEncodingResponse = self._urlOpener.GET( fuzzableRequest.getURL(), headers=headers, useCache=True )
        
            if ifResponse.getCode() == 404 or translateResponse.getCode() == 404 or\
            lockResponse.getCode() == 404 or transferEncodingResponse.getCode() == 404:
                self._reportFinding('URLScan', lockResponse)

    
    def _reportFinding( self, name, response ):
        '''
        Creates a information object based on the name and the response parameter and
        saves the data in the kb.
        '''
        i = info.info()
        i.setURL( response.getURL() )
        i.setId( response.id )
        i.setDesc( 'The remote web server seems to have a '+name+'.' )
        i.setName('Found '+name)
        kb.kb.append( self, name, i )
        om.out.information( i.getDesc() )

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
        return ['discovery.afd']

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        Try to fingerprint the Web Application Firewall that is running on the remote end.
        
        Please note that the detection of the WAF is performed by the discovery.afd plugin ( afd stands
        for Active Filter Detection).
        '''
