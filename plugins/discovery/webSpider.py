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
from core.data.parsers.urlParser import url_object

from core.controllers.misc.levenshtein import relative_distance_ge

from core.controllers.coreHelpers.fingerprint_404 import is_404
import core.data.kb.config as cf
from core.data.fuzzer.formFiller import smartFill
from core.data.fuzzer.fuzzer import createRandAlpha
import core.data.dc.form as form
import core.data.request.httpPostDataRequest as httpPostDataRequest
from core.data.request.variant_identification import are_variants

from core.data.bloomfilter.pybloom import ScalableBloomFilter
from core.data.db.temp_persist import disk_list

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

import re

IS_EQUAL_RATIO = 0.90
MAX_VARIANTS = 5


class webSpider(baseDiscoveryPlugin):
    '''
    Crawl the web application.
    
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
        # TODO: param 'text_factory' *MUST* be removed when the toolkit fully
        # supports unicode
        self._already_crawled = disk_list(text_factory=str)
        self._already_filled_form = ScalableBloomFilter()

        # User configured variables
        self._ignore_regex = ''
        self._follow_regex = '.*'
        self._only_forward = False
        self._compileRE()

    def discover(self, fuzzableRequest ):
        '''
        Searches for links on the html.

        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        om.out.debug( 'webSpider plugin is testing: ' + fuzzableRequest.getURL() )
        
        if self._first_run:
            # I have to set some variables, in order to be able to code the "onlyForward" feature
            self._first_run = False
            self._target_urls = [ i.getDomainPath() for i in cf.cf.getData('targets') ]
            self._target_domain = cf.cf.getData('targets')[0].getDomain()
        
        # If its a form, then smartFill the Dc.
        original_dc = fuzzableRequest.getDc()
        if isinstance( fuzzableRequest, httpPostDataRequest.httpPostDataRequest ):
            
            # TODO!!!!!!
            if fuzzableRequest.getURL() in self._already_filled_form:
                return []
            else:
                self._already_filled_form.add( fuzzableRequest.getURL() )
                
            to_send = original_dc.copy()
            for parameter_name in to_send:
                
                # I do not want to mess with the "static" fields
                if isinstance( to_send, form.form ):
                    if to_send.getType(parameter_name) in ['checkbox', 'file', 'radio', 'select']:
                        continue
                
                #
                #   Set all the other fields, except from the ones that have a value set (example:
                #   hidden fields like __VIEWSTATE).
                #                
                for element_index in xrange(len(to_send[parameter_name])):
                    
                    #   should I ignore it because it already has a value?
                    if to_send[parameter_name][element_index] != '':
                        continue
                    
                    #   smartFill it!
                    to_send[ parameter_name ][element_index] = smartFill( parameter_name )
                    
            fuzzableRequest.setDc( to_send )

        self._fuzzableRequests = []
        response = None

        try:
            response = self._sendMutant( fuzzableRequest, analyze=False )
        except KeyboardInterrupt,e:
            raise e
        else:
            #
            #   Simply ignore 401 responses, because they might bring problems
            #   if I keep crawling them!
            #
            if response.getCode() == 401:
                return []
                
            #
            # Note: I WANT to follow links that are in the 404 page.
            #
            
            # Modified when I added the pdfParser
            # I had to add this x OR y stuff, just because I dont want the SGML parser to analyze
            # a image file, its useless and consumes CPU power.
            if response.is_text_or_html() or response.is_pdf() or response.is_swf():
                originalURL = response.getRedirURI()
                try:
                    documentParser = dpCache.dpc.getDocumentParserFor( response )
                except w3afException, w3:
                    msg = 'Failed to find a suitable document parser.'
                    msg += ' Exception: "' + str(w3) +'".'
                    om.out.debug( msg )
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
                    directories = response.getURL().getDirectories()
                    parsed_references.extend( directories )
                    parsed_references = list( set( parsed_references ) )

                    references = parsed_references + re_references
                    references = list( set( references ) )
                    
                    # Filter only the references that are inside the target domain
                    # I don't want w3af sending request to 3rd parties!
                    references = [ r for r in references if r.getDomain() == self._target_domain]
                            
                    # Filter the URL's according to the configured regular expressions
                    references = [ r for r in references if self._compiled_follow_re.match( r.url_string ) ]
                    references = [ r for r in references if not self._compiled_ignore_re.match( r.url_string )]
                                          
                    # work with the parsed references and report broken links
                    # then work with the regex references and DO NOT report broken links
                    for ref in references:
                        
                        if self._need_more_variants(ref):
                            
                            self._already_crawled.append(ref)
                            
                            possibly_broken = ref in re_references and not ref in parsed_references
                            targs = (ref, fuzzableRequest, originalURL, possibly_broken)
                            self._tm.startFunction( target=self._verify_reference, args=targs, \
                                                                ownerObj=self )
            
        self._tm.join( self )
        
        return self._fuzzableRequests
    
    
    def _need_more_variants(self, new_reference):
        '''
        @new_reference: The new URL that we want to see if its a variant of at most MAX_VARIANTS
        references stored in self._already_crawled.
        
        @return: True if I need more variants of ref.
        
        Basically, the idea is to crawl the whole website, but if we are crawling a site like
        youtube.com that has A LOT of links with the form: 
            - http://www.youtube.com/watch?v=xwLNu5MHXFs
            - http://www.youtube.com/watch?v=JEzjwifH4ts
            - ...
            - http://www.youtube.com/watch?v=something_here
        
        Then we don't actually want to follow all the links to all the videos! So we are going
        to follow a decent number of variant URLs (in this case, video URLs) to see if we can
        find something interesting in those links, but after a fixed number of variants, we will
        start ignoring all those variants.
        '''
        number_of_variants = 0
        #    TODO: The self._already_crawled should be an ORM instead of a simple
        #    disk_list, so I could iterate through all the results and avoid having
        #    to create the url_object() using parsing again.
        for reference in self._already_crawled:
            if are_variants( url_object(reference) , new_reference):
                number_of_variants += 1
                
            if number_of_variants > MAX_VARIANTS:
                msg = 'Ignoring new reference "' + new_reference + '" (it is simply a variant).'
                om.out.debug( msg )
                return False
            
        return True
    
    def _verify_reference( self, reference, original_request, originalURL, possibly_broken ):
        '''
        This method GET's every new link and parses it in order to get new links and forms.
        '''
        fuzzable_request_list = []
        is_forward = self._is_forward(reference)
        if not self._only_forward or is_forward:
            response = None
            #
            #   Remember that this "breaks" the useCache=True in most cases!
            #
            #headers = { 'Referer': originalURL }
            #
            #   But this does not, and it is friendlier that simply ignoring the referer
            #
            referer = originalURL.baseUrl()
            if not referer.url_string.endswith('/'):
                referer += '/'
            headers = { 'Referer': referer }
            
            try:
                response = self._urlOpener.GET( reference, useCache=True, headers= headers)
            except KeyboardInterrupt,e:
                raise e
            except w3afException,w3:
                om.out.error( str(w3) )
            else:
                # Note: I WANT to follow links that are in the 404 page, but if the page
                # I fetched is a 404... I should ignore it.
                if is_404( response ):
                    #
                    # add_self == False, because I don't want to return a 404 to the core
                    #
                    fuzzable_request_list = self._createFuzzableRequests( response, 
                                                                request=original_request, add_self = False)
                    if not possibly_broken:
                        self._brokenLinks.append( (response.getURL(), original_request.getURI()) )
                else:
                    if possibly_broken:
                        #
                        #   Now... the caller is telling us that this link is possibly broken. This
                        #   means that it came from a regular expression, or something that
                        #   usually introduces "false positives". So what I'm going to do is to
                        #   perform one more request to the same directory but with a different
                        #   filename, and then compare it to what we got in the first request.
                        #
                        #   Fixes this:
                        '''
                        /es/ga.js/google-analytics.com
                        /ga.js/google-analytics.com
                        /es/ga.js/google-analytics.com/ga.js/google-analytics.com/ga.js
                        /ga.js/google-analytics.com/google-analytics.com/ga.js/
                        /es/ga.js/google-analytics.com/google-analytics.com/ga.js/
                        /es/ga.js/google-analytics.com/google-analytics.com/
                        /es/ga.js/google-analytics.com/google-analytics.com/google-analytics.com/ga.js
                        /ga.js/google-analytics.com/google-analytics.com/ga.js
                        /services/google-analytics.com/google-analytics.com/
                        /services/google-analytics.com/google-analytics.com/google-analytics.com/ga.js
                        /es/ga.js/google-analytics.com/ga.js/google-analytics.com/ga.js/
                        /ga.js/google-analytics.com/ga.js/google-analytics.com/ga.js/
                        /ga.js/google-analytics.com/ga.js/google-analytics.com/
                        /ga.js/google-analytics.com/ga.js/google-analytics.com/google-analytics.com/ga.js
                        '''
                        filename = reference.getFileName()
                        if filename:
                            
                            new_reference = reference.copy()
                            new_reference.setFileName( createRandAlpha(3) + filename )
                            
                            check_response = self._urlOpener.GET( new_reference, useCache=True,
                                                                  headers= headers)
                            resp_body = response.getBody()
                            check_resp_body = check_response.getBody()

                            if relative_distance_ge(resp_body,
                                                    check_resp_body, IS_EQUAL_RATIO):
                                # If they are equal, then they are both a 404 (or something invalid)
                                #om.out.debug( reference + ' was broken!')
                                return
                            
                            else:
                                # The URL was possibly_broken, but after testing we found out that
                                # it was not, so not we use it!
                                om.out.debug('Adding relative reference "' + reference + '" to the response.')
                                fuzzable_request_list.extend( self._createFuzzableRequests( response, request=original_request ) )
                
                    else: # Not possibly_broken:
                        fuzzable_request_list = self._createFuzzableRequests( response, request=original_request )
                
                # Process the list.
                for fuzzableRequest in fuzzable_request_list:
                    fuzzableRequest.setReferer( referer )
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
                    om.out.information('- ' + broken + ' [ referenced from: ' + where + ' ]')
    
    def _is_forward( self, reference ):
        '''
        Check if the reference is inside the target directories.
        
        @return: True if inside.
        '''
#        if not self._only_forward:
#            return True
#        else:
            # I have to work :S
        is_forward = False
        for domain_path in self._target_urls:
            if reference.url_string.startswith( domain_path.url_string ):
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
        self._only_forward = optionsMap['onlyForward'].getValue()
        self._ignore_regex = optionsMap['ignoreRegex'].getValue()
        self._follow_regex = optionsMap['followRegex'].getValue()
        self._compileRE()
    
    def _compileRE( self ):
        '''
        Now we compile the regular expressions that are going to be
        used to ignore or follow links.
        '''
        #
        #   If the self._ignore_regex is '' then I don't have to ignore anything. To be able to do
        #   that, I simply compile an re with "abc" as the pattern.
        #
        if self._ignore_regex != '':
            try:
                self._compiled_ignore_re = re.compile( self._ignore_regex )
            except:
                msg = 'You specified an invalid regular expression: "' + self._ignore_regex + '".'
                raise w3afException(msg)
        else:
            self._compiled_ignore_re = re.compile( 'abc' )

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
        return [ 'grep.httpAuthDetect', ]
            
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
        
        By default ignoreRegex is an empty string (nothing is ignored) and followRegex is '.*' ( everything is
        followed ). Both regular expressions are normal regular expressions that are compiled with
        the python's re module.
        
        The regular expressions are applied to the URLs that are found using the match function.
        '''
