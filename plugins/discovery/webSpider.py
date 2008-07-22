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
from core.data.getResponseType import isPDF, isTextOrHtml
from core.data.parsers.urlParser import getDomain
from core.controllers.w3afException import w3afException
import core.data.parsers.urlParser as urlParser
from core.data.fuzzer.formFiller import smartFill
import core.data.request.httpPostDataRequest as httpPostDataRequest
import re

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

class webSpider(baseDiscoveryPlugin):
    '''
    Crawl the whole site to find new URLs
    
    @author: Andres Riancho ( andres.riancho@gmail.com )  
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._compiledIgnoreRe = None
        self._compiledFollowRe = None
        self._brokenLinks = []
        self._fuzzableRequests = []
        
        # User configured variables
        self._ignoreRegex = 'None'
        self._followRegex = '.*'
        self._onlyForward = False
        self._compileRE()
        
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
                originalURL = response.getRedirURI()
                try:
                    documentParser = dpCache.dpc.getDocumentParserFor( response )
                except w3afException:
                    # Failed to find a suitable document parser.
                    pass
                else:
                    references = documentParser.getReferences()
                    
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
                        targs = (ref, fuzzableRequest, originalURL)
                        self._tm.startFunction( target=self._verifyReferences, args=targs, ownerObj=self )
            
        self._tm.join( self )
            
        # Restore the Dc value
        fuzzableRequest.setDc( originalDc )
        
        return self._fuzzableRequests
        
    def _verifyReferences( self, reference, originalRequest, originalURL ):
        '''
        This method GET's every new link and parses it in order to get new links and forms.
        '''
        if getDomain( reference ) == getDomain( originalURL ):
            if self._isForward( reference, originalURL ):
                response = None
                headers = { 'Referer': originalURL }
                
                try:
                    response = self._urlOpener.GET( reference, useCache=True, headers= headers, getSize=True )
                except KeyboardInterrupt,e:
                    raise e
                except w3afException,w3:
                    om.out.error( str(w3) )
                else:
                    # Note: I WANT to follow links that are in the 404 page, but if the page I fetched is a 404...
                    # I should ignore it.
                    if self.is404( response ):
                        fuzzableRequestList = self._createFuzzableRequests( response, addSelf=False )
                        self._brokenLinks.append( (response.getURL(), originalRequest.getURI()) )
                    else:
                        fuzzableRequestList = self._createFuzzableRequests( response, addSelf=True )
                    
                    # Process the list.
                    for fuzzableRequest in fuzzableRequestList:
                        fuzzableRequest.setReferer( originalURL )
                        self._fuzzableRequests.append( fuzzableRequest )
    
    def end( self ):
        '''
        Called when the process ends, prints out the list of broken links.
        '''
        if len(self._brokenLinks):
            reported = []
            om.out.information('The following is a list of broken links that were found by the webSpider plugin:')
            for broken, where in self._brokenLinks:
                if (broken, where) not in reported:
                    reported.append( (broken, where) )
                    om.out.information('- ' + broken + ' [ ' + where + ' ]')
    
    def _isForward( self, reference, originalURL ):
        '''
        Check if the reference is inside the original URL directory
        @return: True if inside.
        '''
        if not self._onlyForward:
            return True
        else:
            # I have to work :S
            joinedURL = urlParser.urlJoin( originalURL, reference )
            if joinedURL.startswith( urlParser.getDomainPath( originalURL )  ):
                return True
            else:
                return False
                
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'When spidering, only search directories inside the one that was given as a parameter'
        o1 = option('onlyForward', self._onlyForward, d1, 'boolean')
        
        d2 = 'When spidering, only follow links that match this regular expression (ignoreRegex has precedence over followRegex)'
        o2 = option('followRegex', self._followRegex, d2, 'string')
        
        d3 = 'When spidering, DO NOT follow links that match this regular expression (has precedence over followRegex)'
        o3 = option('ignoreRegex', self._ignoreRegex, d3, 'string')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        return ol
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._onlyForward = optionsMap['onlyForward'].getValue()
        self._ignoreRegex = optionsMap['ignoreRegex'].getValue()
        self._followRegex = optionsMap['followRegex'].getValue()
        
        self._compileRE()
    
    def _compileRE( self ):
        '''
        Now we compile the regular expressions that are going to be
        used to ignore or follow links.
        '''
        try:
            self._compiledIgnoreRe = re.compile( self._ignoreRegex )
        except:
            raise w3afException('You specified an invalid regular expression: "' + self._ignoreRegex + '".')

        try:
            self._compiledFollowRe = re.compile( self._followRegex )
        except:
            raise w3afException('You specified an invalid regular expression: "' + self._followRegex + '".')
        
        
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
