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

import core.controllers.outputManager as om

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.w3afException import w3afException

import core.data.parsers.dpCache as dpCache
from core.data.parsers.urlParser import getDomain
import core.data.parsers.urlParser as urlParser

import core.data.kb.knowledgeBase as kb
import core.data.kb.config as cf
from core.data.fuzzer.formFiller import smartFill
import core.data.request.httpPostDataRequest as httpPostDataRequest

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

import re


class webSpider(baseDiscoveryPlugin):
    '''
    Crawl the whole site to find new URLs
    
    @author: Andres Riancho ( andres.riancho@gmail.com )  
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)

        # Internal variables
        self._compiled_ignore_re = None
        self._compiled_follow_re = None
        self._brokenLinks = []
        self._fuzzableRequests = []
        self._first_run = True

        # User configured variables
        self._ignore_regex = 'None'
        self._follow_regex = '.*'
        self._only_forward = False
        self._compileRE()
        self._url_parameter = None

    def discover(self, fuzzableRequest ):
        '''
        Searches for links on the html.

        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        om.out.debug( 'webSpider plugin is testing: ' + fuzzableRequest.getURL() )
        
        if self._first_run:
            # I have to set some variables, in order to be able to code the "onlyForward" feature
            self._first_run = False
            self._target_urls = [ urlParser.getDomainPath(i) for i in cf.cf.getData('targets') ]
            

        # Init some internal variables
        self.is404 = kb.kb.getData( 'error404page', '404' )

        # Set the URL parameter if necessary
        if self._url_parameter != None:
            fuzzableRequest.setURL(urlParser.setParam(fuzzableRequest.getURL(), self._url_parameter))
            fuzzableRequest.setURI(urlParser.setParam(fuzzableRequest.getURI(), self._url_parameter))

        # If its a form, then smartFill the Dc.
        original_dc = fuzzableRequest.getDc()
        if isinstance( fuzzableRequest, httpPostDataRequest.httpPostDataRequest ):
            to_send = original_dc.copy()
            for parameter in to_send:
                to_send[ parameter ] = smartFill( parameter )
            fuzzableRequest.setDc( to_send )

        self._fuzzableRequests = []
        response = None

        try:
            response = self._sendMutant( fuzzableRequest, analyze=False )
        except KeyboardInterrupt,e:
            raise e
        else:
            # Note: I WANT to follow links that are in the 404 page.
            
            # Modified when I added the pdfParser
            # I had to add this x OR y stuff, just because I dont want the SGML parser to analyze
            # a image file, its useless and consumes cpu power.
            if response.is_text_or_html() or response.is_pdf() or response.is_swf():
                originalURL = response.getRedirURI()
                if self._url_parameter != None:
                    originalURL = urlParser.setParam(originalURL, self._url_parameter)
                try:
                    documentParser = dpCache.dpc.getDocumentParserFor( response )
                except w3afException, w3:
                    msg = 'Failed to find a suitable document parser.'
                    msg += ' Exception: "' + str(w3) +'".'
                    om.out.error( msg )
                else:
                    # Note:
                    # - With parsed_references I'm 100% that it's really something in the HTML
                    # that the developer intended to add.
                    #
                    # - The re_references are the result of regular expressions, which in some cases
                    # are just false positives.
                    parsed_references, re_references = documentParser.getReferences()
                    
                    # I also want to analyze all directories, if the URL I just fetched is:
                    # http://localhost/a/b/c/f00.php I want to GET:
                    # http://localhost/a/b/c/
                    # http://localhost/a/b/
                    # http://localhost/a/
                    # http://localhost/
                    # And analyze the responses...
                    directories = urlParser.getDirectories( response.getURL() )
                    parsed_references.extend( directories )
                    parsed_references = list( set( parsed_references ) )
                    
                    # Filter the URL's according to the configured regular expressions
                    parsed_references = [ r for r in parsed_references if self._compiled_follow_re.match( r ) ]
                    parsed_references = [ r for r in parsed_references if not self._compiled_ignore_re.match( r )]
                    
                    re_references = [ r for r in re_references if self._compiled_follow_re.match( r ) ]
                    re_references = [ r for r in re_references if not self._compiled_ignore_re.match( r )]
          
                    # work with the parsed references and report broken links
                    for ref in parsed_references:
                        if self._url_parameter != None:
                            ref = urlParser.setParam(ref, self._url_parameter)
                        targs = (ref, fuzzableRequest, originalURL, True)
                        self._tm.startFunction( target=self._verifyReferences, args=targs, \
                                                            ownerObj=self )
                                                            
                    # work with the parsed references and DO NOT report broken links
                    for ref in re_references:
                        if self._url_parameter != None:
                            ref = urlParser.setParam(ref, self._url_parameter)
                        targs = (ref, fuzzableRequest, originalURL, False)
                        self._tm.startFunction( target=self._verifyReferences, args=targs, \
                                                            ownerObj=self )
            
        self._tm.join( self )
            
        # Restore the Dc value
        fuzzableRequest.setDc( original_dc )
        
        return self._fuzzableRequests
        
    def _verifyReferences( self, reference, originalRequest, originalURL, report_broken ):
        '''
        This method GET's every new link and parses it in order to get new links and forms.
        '''
        if getDomain( reference ) == getDomain( originalURL ):
            if self._isForward( reference ):
                
                response = None
                headers = { 'Referer': originalURL }
                
                try:
                    response = self._urlOpener.GET( reference, useCache=True, headers= headers, \
                                                                    getSize=True)
                except KeyboardInterrupt,e:
                    raise e
                except w3afException,w3:
                    om.out.error( str(w3) )
                else:
                    # Note: I WANT to follow links that are in the 404 page, but if the page
                    # I fetched is a 404... I should ignore it.
                    if self.is404( response ):
                        fuzzableRequestList = self._createFuzzableRequests( response, addSelf=False)
                        if report_broken:
                            self._brokenLinks.append( (response.getURL(), originalRequest.getURI()) )
                    else:
                        fuzzableRequestList = self._createFuzzableRequests( response, addSelf=True )
                    
                    # Process the list.
                    for fuzzableRequest in fuzzableRequestList:
                        if self._url_parameter != None:
                            fuzzableRequest.setURL(urlParser.setParam(fuzzableRequest.getURL(), self._url_parameter))
                            fuzzableRequest.setURI(urlParser.setParam(fuzzableRequest.getURI(), self._url_parameter))
                        fuzzableRequest.setReferer( originalURL )
                        self._fuzzableRequests.append( fuzzableRequest )
    
    def end( self ):
        '''
        Called when the process ends, prints out the list of broken links.
        '''
        if len(self._brokenLinks):
            reported = []
            msg = 'The following is a list of broken links that were found by the webSpider plugin:'
            om.out.information(msg)
            for broken, where in self._brokenLinks:
                if (broken, where) not in reported:
                    reported.append( (broken, where) )
                    om.out.information('- ' + broken + ' [ ' + where + ' ]')
    
    def _isForward( self, reference ):
        '''
        Check if the reference is inside the target directories.
        
        @return: True if inside.
        '''
        if not self._only_forward:
            return True
        else:
            # I have to work :S
            is_forward = False
            for domain_path in self._target_urls:
                if reference.startswith(domain_path):
                    is_forward = True
                    break
            return is_forward
                
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'When spidering, only search directories inside the one that was given as target'
        o1 = option('onlyForward', self._only_forward, d1, 'boolean')
        
        d2 = 'When spidering, only follow links that match this regular expression '
        d2 +=  '(ignoreRegex has precedence over followRegex)'
        o2 = option('followRegex', self._follow_regex, d2, 'string')
        
        d3 = 'When spidering, DO NOT follow links that match this regular expression '
        d3 += '(has precedence over followRegex)'
        o3 = option('ignoreRegex', self._ignore_regex, d3, 'string')
        
        d4 = 'Append the given parameter to new URLs found by the spider.'
        d4 += ' Example: http://www.foobar.com/index.jsp;<parameter>?id=2'
        o4 = option('urlParameter', self._url_parameter, d4, 'string')    

        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        return ol
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._only_forward = optionsMap['onlyForward'].getValue()
        self._ignore_regex = optionsMap['ignoreRegex'].getValue()
        self._follow_regex = optionsMap['followRegex'].getValue()
        self._url_parameter = optionsMap['urlParameter'].getValue()
        self._compileRE()
    
    def _compileRE( self ):
        '''
        Now we compile the regular expressions that are going to be
        used to ignore or follow links.
        '''
        try:
            self._compiled_ignore_re = re.compile( self._ignore_regex )
        except:
            msg = 'You specified an invalid regular expression: "' + self._ignore_regex + '".'
            raise w3afException(msg)

        try:
            self._compiled_follow_re = re.compile( self._follow_regex )
        except:
            msg = 'You specified an invalid regular expression: "' + self._follow_regex + '".'
            raise w3afException(msg)
        
        
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
            - urlParameter

        IgnoreRegex and followRegex are commonly used to configure the webSpider to spider
        all URLs except the "logout" or some other more exciting link like "Reboot Appliance"
        that would make the w3af run finish without the expected result.
        
        By default ignoreRegex is 'None' (nothing is ignored) and followRegex is '.*' ( everything is
        followed ). Both regular expressions are normal regular expressions that are compiled with
        the python's re module.
        '''
