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

import itertools
import re

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.coreHelpers.fingerprint_404 import is_404
from core.controllers.misc.levenshtein import relative_distance_ge
from core.controllers.w3afException import w3afException, \
    w3afMustStopOnUrlError
from core.data.bloomfilter.bloomfilter import scalable_bloomfilter
from core.data.db.temp_persist import disk_list as DiskList
from core.data.fuzzer.formFiller import smartFill
from core.data.fuzzer.fuzzer import createRandAlpha
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.data.request.httpPostDataRequest import httpPostDataRequest as \
    HttpPostDataRequest
from core.data.request.variant_identification import are_variants
import core.controllers.outputManager as om
import core.data.dc.form as form
import core.data.kb.config as cf
import core.data.parsers.dpCache as dpCache

IS_EQUAL_RATIO = 0.90
MAX_VARIANTS = 40


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
        self._already_crawled = DiskList()
        self._already_filled_form = scalable_bloomfilter()

        # User configured variables
        self._ignore_regex = ''
        self._follow_regex = '.*'
        self._only_forward = False
        self._compileRE()

    def discover(self, fuzzableRequest):
        '''
        Searches for links on the html.

        @param fuzzableRequest: A fuzzableRequest instance that contains
            (among other things) the URL to test.
        '''
        om.out.debug('webSpider plugin is testing: %s' %
                     fuzzableRequest.getURL())
        
        if self._first_run:
            # I have to set some variables, in order to be able to code
            # the "onlyForward" feature
            self._first_run = False
            self._target_urls = [i.getDomainPath() for i in cf.cf.getData('targets')]
            self._target_domain = cf.cf.getData('targets')[0].getDomain()
        
        # If its a form, then smartFill the Dc.
        if isinstance(fuzzableRequest, HttpPostDataRequest):
            
            # TODO: !!!!!!
            if fuzzableRequest.getURL() in self._already_filled_form:
                return []
            
            self._already_filled_form.add(fuzzableRequest.getURL())
            
            to_send = fuzzableRequest.getDc().copy()
            
            for param_name in to_send:
                
                # I do not want to mess with the "static" fields
                if isinstance(to_send, form.form):
                    if to_send.getType(param_name) in ('checkbox', 'file',
                                                       'radio', 'select'):
                        continue
                
                # Set all the other fields, except from the ones that have a
                # value set (example: hidden fields like __VIEWSTATE).
                for elem_index in xrange(len(to_send[param_name])):
                    
                    # Should I ignore it because it already has a value?
                    if to_send[param_name][elem_index] != '':
                        continue
                    
                    # SmartFill it!
                    to_send[param_name][elem_index] = smartFill(param_name)
                    
            fuzzableRequest.setDc(to_send)

        self._fuzzableRequests = []
        response = None

        try:
            response = self._sendMutant(fuzzableRequest, analyze=False)
        except KeyboardInterrupt:
            raise
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
            # I had to add this x OR y stuff, just because I don't want 
            # the SGML parser to analyze a image file, its useless and
            # consumes CPU power.
            if response.is_text_or_html() or response.is_pdf() or \
                response.is_swf():
                originalURL = response.getRedirURI()
                try:
                    doc_parser = dpCache.dpc.getDocumentParserFor(response)
                except w3afException, w3:
                    om.out.debug('Failed to find a suitable document parser. '
                                 'Exception "%s"' % w3)
                else:
                    # Note:
                    # - With parsed_refs I'm 100% that it's really 
                    # something in the HTML that the developer intended to add.
                    #
                    # - The re_refs are the result of regular expressions,
                    # which in some cases are just false positives.
                    parsed_refs, re_refs = doc_parser.getReferences()
                    
                    # I also want to analyze all directories, if the URL I just
                    # fetched is:
                    # http://localhost/a/b/c/f00.php I want to GET:
                    # http://localhost/a/b/c/
                    # http://localhost/a/b/
                    # http://localhost/a/
                    # http://localhost/
                    # And analyze the responses...
                    dirs = response.getURL().getDirectories()
                    seen = set()
                    only_re_refs = set(re_refs) - set(dirs + parsed_refs)
                    
                    for ref in itertools.chain(dirs, parsed_refs, re_refs):
                        
                        if ref in seen:
                            continue
                        seen.add(ref)
                        
                        # I don't want w3af sending requests to 3rd parties!
                        if ref.getDomain() != self._target_domain:
                            continue
                        
                        # Filter the URL's according to the configured regexs
                        urlstr = ref.url_string
                        if not self._compiled_follow_re.match(urlstr) or \
                            self._compiled_ignore_re.match(urlstr):
                            continue
                        
                        # Work with the parsed references and report broken
                        # links. Then work with the regex references and DO NOT
                        # report broken links
                        if self._need_more_variants(ref):
                            self._already_crawled.append(ref)
                            possibly_broken = ref in only_re_refs
                            targs = (ref, fuzzableRequest, originalURL,
                                     possibly_broken)
                            self._tm.startFunction(
                                    target=self._verify_reference,
                                    args=targs, ownerObj=self)
            
        self._tm.join(self)
        
        return self._fuzzableRequests
    
    
    def _need_more_variants(self, new_reference):
        '''
        @param new_reference: The new URL that we want to see if its a variant
            of at most MAX_VARIANTS references stored in self._already_crawled.
        
        @return: True if I need more variants of ref.
        
        Basically, the idea is to crawl the whole website, but if we are
        crawling a site like youtube.com that has A LOT of links with the form: 
            - http://www.youtube.com/watch?v=xwLNu5MHXFs
            - http://www.youtube.com/watch?v=JEzjwifH4ts
            - ...
            - http://www.youtube.com/watch?v=something_here
        
        Then we don't actually want to follow all the links to all the videos!
        So we are going to follow a decent number of variant URLs (in this
        case, video URLs) to see if we can find something interesting in those
        links, but after a fixed number of variants, we will start ignoring all
        those variants.
        '''
        number_of_variants = 0
        
        # TODO: The self._already_crawled should be an ORM instead of a simple
        # disk_list, so I could iterate through all the results and avoid
        # having to create the url_object() using parsing again.
        for reference in self._already_crawled:
            if are_variants(reference, new_reference):
                number_of_variants += 1
                
            if number_of_variants > MAX_VARIANTS:
                msg = ('Ignoring new reference "%s" (it is simply a variant).'
                       % new_reference)
                om.out.debug(msg)
                return False
            
        return True
    
    def _verify_reference(self, reference, original_request,
                          originalURL, possibly_broken):
        '''
        This method GET's every new link and parses it in order to get
        new links and forms.
        '''
        fuzz_req_list = []
        is_forward = self._is_forward(reference)
        if not self._only_forward or is_forward:
            resp = None
            #
            # Remember that this "breaks" the useCache=True in most cases!
            #     headers = { 'Referer': originalURL }
            #
            # But this does not, and it is friendlier that simply ignoring the
            # referer
            #
            referer = originalURL.baseUrl()
            if not referer.url_string.endswith('/'):
                referer += '/'
            headers = {'Referer': referer}
            
            try:
                resp = self._urlOpener.GET(reference, useCache=True, 
                                           headers=headers)
            except KeyboardInterrupt:
                raise
            except w3afMustStopOnUrlError:
                pass
            else:
                # Note: I WANT to follow links that are in the 404 page, but
                # if the page I fetched is a 404 then it should be ignored.
                if is_404(resp):
                    # add_self == False, because I don't want to return a 404
                    # to the core
                    fuzz_req_list = self._createFuzzableRequests(resp,
                                     request=original_request, add_self=False)
                    if not possibly_broken:
                        t = (resp.getURL(), original_request.getURI())
                        self._brokenLinks.append(t)
                else:
                    if possibly_broken:
                        #
                        # Now the caller is telling us that this link is 
                        # possibly broken. This means that it came from a 
                        # regular expression, or something that usually 
                        # introduces "false positives". So what I'm going to do
                        # is to perform one more request to the same directory
                        # but with a different filename, and then compare it to
                        # what we got in the first request.
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
                            new_reference.setFileName(createRandAlpha(3) +
                                                      filename)
                            
                            check_response = self._urlOpener.GET(new_reference,
                                                useCache=True, headers=headers)
                            resp_body = resp.getBody()
                            check_resp_body = check_response.getBody()

                            if relative_distance_ge(resp_body,
                                            check_resp_body, IS_EQUAL_RATIO):
                                # If they are equal, then they are both a 404
                                # (or something invalid)
                                # om.out.debug(reference + ' was broken!')
                                return
                            
                            else:
                                # The URL was possibly_broken, but after 
                                # testing we found out that it was not, so now
                                # we use it!
                                om.out.debug('Adding relative reference "%s" '
                                             'to the resp.' % reference)
                                frlist = self._createFuzzableRequests(
                                               resp, request=original_request)
                                fuzz_req_list.extend(frlist)
                
                    else: # Not possibly_broken:
                        fuzz_req_list = self._createFuzzableRequests(resp,
                                                     request=original_request)
                
                # Process the list.
                for fuzz_req in fuzz_req_list:
                    fuzz_req.setReferer(referer)
                    self._fuzzableRequests.append(fuzz_req)
    
    def end(self):
        '''
        Called when the process ends, prints out the list of broken links.
        '''
        if len(self._brokenLinks):
            reported = []
            om.out.information('The following is a list of broken links that '
                               'were found by the webSpider plugin:')
            for broken, where in self._brokenLinks:
                if (broken, where) not in reported:
                    reported.append((broken, where))
                    om.out.information('- %s [ referenced from: %s ]' %
                                       (broken, where))
    
    def _is_forward(self, reference):
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
            if reference.url_string.startswith(domain_path.url_string):
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
    
    def _compileRE(self):
        '''
        Compile the regular expressions that are going to be used to ignore
        or follow links.
        '''
        # If the self._ignore_regex is empty then I don't have to ignore
        # anything. To be able to do that, I simply compile an re with "abc"
        # as the pattern.
        if self._ignore_regex:
            try:
                self._compiled_ignore_re = re.compile(self._ignore_regex)
            except:
                raise w3afException('You specified an invalid regular '
                                    'expression: "%s".' % self._ignore_regex)
        else:
            self._compiled_ignore_re = re.compile('abc')

        try:
            self._compiled_follow_re = re.compile(self._follow_regex)
        except:
            raise w3afException('You specified an invalid regular expression: '
                                '"%s".' % self._follow_regex)
        
        
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
