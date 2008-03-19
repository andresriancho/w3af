'''
webSpider.py

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

import core.data.parsers.dpCache as dpCache
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.kb.knowledgeBase as kb
import core.controllers.outputManager as om
from core.data.getResponseType import *
from core.data.parsers.urlParser import getDomain
from core.controllers.w3afException import w3afException
import core.data.parsers.urlParser as urlParser
from core.data.fuzzer.formFiller import smartFill
import core.data.request.httpPostDataRequest as httpPostDataRequest
import re

class webSpider(baseDiscoveryPlugin):
    '''
    Crawl the whole site to find new URLs
    
    @author: Andres Riancho ( andres.riancho@gmail.com )  
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._onlyForward = False
        
        self._ignoreRegex = 'None'
        self._followRegex = '.*'
        self._compileRE()
        
        self._brokenLinks = []
        
    def discover(self, fuzzableRequest ):
        '''
        Searches for links on the html.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        om.out.debug( 'webSpider plugin is testing: ' + fuzzableRequest.getURL() )
        
        # Init some internal variables
        self.is404 = kb.kb.getData( 'error404page', '404' )
        
        # If its a form, then smartFill the Dc.
        originalDc = fuzzableRequest.getDc()
        if isinstance( fuzzableRequest, httpPostDataRequest.httpPostDataRequest ):
            toSend = originalDc.copy()
            for parameter in toSend:
                toSend[ parameter ] = smartFill( parameter )
            fuzzableRequest.setDc( toSend )
        
        self._fuzzableRequests = []
        response = None
        
        try:
            response = self._sendMutant( fuzzableRequest, analyze=False )
        except KeyboardInterrupt,e:
            raise e
        else:
            
            references = []
            # Note: I WANT to follow links that are in the 404 page.
            
            # Modified when I added the pdfParser
            # I had to add this x OR y stuff, just because I dont want the SGML parser to analyze
            # a image file, its useless and consumes cpu power.
            if isTextOrHtml( response.getHeaders() ) or isPDF( response.getHeaders() ):
                self._originalURL = response.getRedirURI()
                dp = dpCache.dpc.getDocumentParserFor( response.getBody(), self._originalURL )
                references = dp.getReferences()
                
                # I also want to analyze all directories, if the URL I just fetched is:
                # http://localhost/a/b/c/f00.php I want to GET:
                # http://localhost/a/b/c/
                # http://localhost/a/b/
                # http://localhost/a/
                # http://localhost/
                # And analyze the responses...
                directories = urlParser.getDirectories( response.getURL() )
                references.extend( directories )
                references = list( set( references ) )
                
                # Filter the URL's according to the configured regular expressions
                references = [ r for r in references if self._compiledFollowRe.match( r ) ]
                references = [ r for r in references if not self._compiledIgnoreRe.match( r )]
                
                for ref in references:
                    targs = (ref, fuzzableRequest)
                    self._tm.startFunction( target=self._verifyReferences, args=targs, ownerObj=self )
            
        self._tm.join( self )
            
        # Restore the Dc value
        fuzzableRequest.setDc( originalDc )
        
        return self._fuzzableRequests
        
    def _verifyReferences( self, reference, originalRequest ):
        
        if getDomain( reference ) == getDomain( self._originalURL ):
            if self._isForward( reference ):
                response = None
                h = { 'Referer': self._originalURL }
                
                try:
                    response = self._urlOpener.GET( reference, useCache=True, headers=h, getSize=True )
                except KeyboardInterrupt,e:
                    raise e
                except w3afException,w:
                    om.out.error( str(w) )
                except Exception,e:
                    raise e
                else:
                    # Note: I WANT to follow links that are in the 404 page, but if the page I fetched is a 404...
                    # I should ignore it.
                    if self.is404( response ):
                        fuzzableRequestList = self._createFuzzableRequests( response, addSelf=False )
                        self._brokenLinks.append( (response.getURL(), originalRequest.getURI()) )
                    else:
                        fuzzableRequestList = self._createFuzzableRequests( response, addSelf=True )
                    
                    # Process the list.
                    for fr in fuzzableRequestList:
                        fr.setReferer( self._originalURL )
                        self._fuzzableRequests.append( fr )
    
    def end( self ):
        '''
        Called when the process ends, prints out the list of broken links.
        '''
        if len(self._brokenLinks):
            reported = []
            om.out.information('The following is a list of broken links that were found by the webSpider plugin:')
            for u,o in self._brokenLinks:
                if (u,o) not in reported:
                    reported.append( (u,o) )
                    om.out.information('- ' + u + ' [ ' + o + ' ]')
    
    def _isForward( self, reference ):
        '''
        Check if the reference is inside the original URL directory
        @return: True if inside.
        '''
        if not self._onlyForward:
            return True
        else:
            # I have to work :S
            joinedURL = urlParser.urlJoin( self._originalURL, reference )
            if joinedURL.startswith( urlParser.getDomainPath( self._originalURL )  ):
                return True
            else:
                return False
        
    
    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/ui/userInterface.dtd
        
        @return: XML with the plugin options.
        ''' 
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
            <Option name="onlyForward">\
                <default>'+str(self._onlyForward)+'</default>\
                <desc>When spidering, only search directories inside the one that was given as a parameter</desc>\
                <type>boolean</type>\
            </Option>\
            <Option name="followRegex">\
                <default>'+self._followRegex+'</default>\
                <desc>When spidering, only follow links that match this regular expression (ignoreRegex has precedence over followRegex)</desc>\
                <type>string</type>\
            </Option>\
            <Option name="ignoreRegex">\
                <default>'+self._ignoreRegex+'</default>\
                <desc>When spidering, DO NOT follow links that match this regular expression (has precedence over followRegex)</desc>\
                <type>string</type>\
            </Option>\
        </OptionList>\
        '

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._onlyForward = optionsMap['onlyForward']
        self._ignoreRegex = optionsMap['ignoreRegex']
        self._followRegex = optionsMap['followRegex']
        
        self._compileRE()
    
    def _compileRE( self ):
        # Now we compile the regular expressions
        self._compiledIgnoreRe = re.compile( self._ignoreRegex )
        self._compiledFollowRe = re.compile( self._followRegex )
        
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return [ 'discovery.allowedMethods' ]
            
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin is a classic web spider, it will request a URL and extract all links and forms
        from the response.
    
        Three configurable parameter exist:
            - onlyForward
            - ignoreRegex
            - followRegex
            
        IgnoreRegex and followRegex are commonly used to configure the webSpider to spider
        all URLs except the "logout" or some other more exciting link like "Reboot Appliance"
        that would make the w3af run finish without the expected result.
        
        By default ignoreRegex is 'None' (nothing is ignored) and followRegex is '.*' ( everything is
        followed ). Both regular expressions are normal regular expressions that are compiled with
        the python's re module.
        '''
