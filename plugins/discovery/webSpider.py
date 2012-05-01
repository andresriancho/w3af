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
from core.controllers.w3afException import w3afException, w3afMustStopOnUrlError
from core.controllers.misc.itertools_toolset import unique_justseen
from core.data.bloomfilter.bloomfilter import scalable_bloomfilter
from core.data.db.temp_shelve import temp_shelve as temp_shelve
from core.data.db.disk_set import disk_set
from core.data.fuzzer.formFiller import smartFill
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.data.request.httpPostDataRequest import httpPostDataRequest as \
    HttpPostDataRequest
import core.controllers.outputManager as om
import core.data.dc.form as form
import core.data.kb.config as cf
import core.data.parsers.dpCache as dpCache

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
        self._broken_links = disk_set()
        self._fuzzable_reqs = disk_set()
        self._first_run = True
        self._known_variants = variant_db()
        self._already_filled_form = scalable_bloomfilter()

        # User configured variables
        self._ignore_regex = ''
        self._follow_regex = '.*'
        self._only_forward = False
        self._compileRE()

    def discover(self, fuzzable_req):
        '''
        Searches for links on the html.

        @param fuzzable_req: A fuzzable_req instance that contains
            (among other things) the URL to test.
        '''
        om.out.debug('webSpider plugin is testing: %s' %
                     fuzzable_req.getURL())
        
        if self._first_run:
            # I have to set some variables, in order to be able to code
            # the "onlyForward" feature
            self._first_run = False
            self._target_urls = [i.getDomainPath() for i in cf.cf.getData('targets')]
            
            #    The following line triggered lots of bugs when the "stop" button
            #    was pressed and the core did this: "cf.cf.save('targets', [])"
            #self._target_domain = cf.cf.getData('targets')[0].getDomain()
            #    Changing it to something awful but bug-free.
            targets = cf.cf.getData('targets')
            if not targets:
                return []
            else:
                self._target_domain = targets[0].getDomain()

        # Clear the previously found fuzzable requests,
        self._fuzzable_reqs.clear()

        #
        # If it is a form, then smartFill the parameters to send something that
        # makes sense and will allow us to cover more code.
        #
        if isinstance(fuzzable_req, HttpPostDataRequest):
            
            if fuzzable_req.getURL() in self._already_filled_form:
                return []

            fuzzable_req = self._fill_form(fuzzable_req)            

        # Send the HTTP request,
        resp = self._sendMutant(fuzzable_req, analyze=False,
                                follow_redir=False)

        # Nothing to do here...        
        if resp.getCode() == 401:
            return []

        fuzz_req_list = self._createFuzzableRequests(
                                             resp,
                                             request=fuzzable_req,
                                             add_self=False
                                             )
        self._fuzzable_reqs.update(fuzz_req_list)

        self._extract_links_and_verify(resp, fuzzable_req)
        
        return self._fuzzable_reqs


    def _extract_links_and_verify(self, resp, fuzzable_req):
        #
        # Note: I WANT to follow links that are in the 404 page.
        #
        
        # Modified when I added the pdfParser
        # I had to add this x OR y stuff, just because I don't want 
        # the SGML parser to analyze a image file, its useless and
        # consumes CPU power.
        if resp.is_text_or_html() or resp.is_pdf() or resp.is_swf():
            originalURL = resp.getRedirURI()
            try:
                doc_parser = dpCache.dpc.getDocumentParserFor(resp)
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
                dirs = resp.getURL().getDirectories()
                only_re_refs = set(re_refs) - set(dirs + parsed_refs)
                
                for ref in unique_justseen(
                               sorted( itertools.chain(dirs, parsed_refs, re_refs) )):
                    
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
                        self._known_variants.append(ref)
                        possibly_broken = ref in only_re_refs
                        args = (ref, fuzzable_req, originalURL,
                                 possibly_broken)
                        self._run_async(meth=self._verify_reference, args=args)
                self._join()
        

    def _fill_form(self, fuzzable_req):
        '''
        Fill the HTTP request form that is passed as fuzzable_req.
        @return: A filled form
        '''
        self._already_filled_form.add(fuzzable_req.getURL())
        
        to_send = fuzzable_req.getDc().copy()
        
        for param_name in to_send:
            
            # I do not want to mess with the "static" fields
            if isinstance(to_send, form.Form):
                if to_send.getType(param_name) in ('checkbox', 'file',
                                                   'radio', 'select'):
                    continue
            
            # Set all the other fields, except from the ones that have a
            # value set (example: hidden fields like __VIEWSTATE).
            for elem_index in xrange(len(to_send[param_name])):
                
                # TODO: Should I ignore it because it already has a value?
                if to_send[param_name][elem_index] != '':
                    continue
                
                # SmartFill it!
                to_send[param_name][elem_index] = smartFill(param_name)
                
        fuzzable_req.setDc(to_send)
        return fuzzable_req 
    
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
        if self._known_variants.need_more_variants( new_reference ):
            return True
        else:
            msg = ('Ignoring new reference "%s" (it is simply a variant).'
                    % new_reference)
            om.out.debug(msg)
            return False
    
    def _verify_reference(self, reference, original_request,
                          originalURL, possibly_broken):
        '''
        This method GET's every new link and parses it in order to get
        new links and forms.
        '''
        is_forward = self._is_forward(reference)
        if not self._only_forward or is_forward:
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
                                           headers=headers, follow_redir=False)
            except w3afMustStopOnUrlError:
                pass
            else:
                fuzz_req_list = []
                # Note: I WANT to follow links that are in the 404 page, but
                # if the page I fetched is a 404 then it should be ignored.
                if is_404(resp):
                    # add_self == False, because I don't want to return a 404
                    # to the core
                    fuzz_req_list = self._createFuzzableRequests(resp,
                                     request=original_request, add_self=False)
                    if not possibly_broken:
                        t = (resp.getURL(), original_request.getURI())
                        self._broken_links.add(t)
                else:
                    om.out.debug('Adding relative reference "%s" '
                                 'to the result.' % reference)
                    frlist = self._createFuzzableRequests(resp, request=original_request)
                    fuzz_req_list.extend(frlist)
                                
                # Process the list.
                for fuzz_req in fuzz_req_list:
                    fuzz_req.setReferer(referer)
                    self._fuzzable_reqs.add(fuzz_req)
    
    def end(self):
        '''
        Called when the process ends, prints out the list of broken links.
        '''
        if len(self._broken_links):
            
            om.out.information('The following is a list of broken links that '
                               'were found by the webSpider plugin:')
            for broken, where in unique_justseen(self._broken_links.ordered_iter()):
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
        @return: A list with the names of the plugins that should be run before the
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

class variant_db(object):
    def __init__(self):
        self._internal_dict = temp_shelve()
        
    def append(self, reference):
        '''
        Called when a new reference is found and we proved that new
        variants are still needed.
        
        @param reference: The reference (as an url_object) to add. This method
        will "normalize" it before adding it to the internal dict.
        '''
        clean_reference = self._clean_reference( reference )
        
        count = self._internal_dict.get( clean_reference, None)
        
        if count is not None:
            self._internal_dict[ clean_reference ] = count + 1
        else:
            self._internal_dict[ clean_reference ] = 1
            
    def _clean_reference(self, reference):
        '''
        This method is VERY dependent on the are_variants method from
        core.data.request.variant_identification , make sure to remember that
        when changing stuff here or there.
        
        What this method does is to "normalize" any input reference string so
        that they can be compared very simply using string match.

        >>> from core.data.parsers.urlParser import url_object
        >>> from core.controllers.misc.temp_dir import create_temp_dir
        >>> _ = create_temp_dir()
        >>> URL = url_object
        
        >>> vdb = variant_db()
        
        >>> vdb._clean_reference(URL('http://w3af.org/'))
        u'http://w3af.org/'
        >>> vdb._clean_reference(URL('http://w3af.org/index.php'))
        u'http://w3af.org/index.php'
        >>> vdb._clean_reference(URL('http://w3af.org/index.php?id=2'))
        u'http://w3af.org/index.php?id=number'
        >>> vdb._clean_reference(URL('http://w3af.org/index.php?id=2&foo=bar'))
        u'http://w3af.org/index.php?id=number&foo=string'
        >>> vdb._clean_reference(URL('http://w3af.org/index.php?id=2&foo=bar&spam='))
        u'http://w3af.org/index.php?id=number&foo=string&spam=string'
         
        '''
        res = reference.getDomainPath() + reference.getFileName()
        
        if reference.hasQueryString():
            
            res += '?'
            qs = reference.querystring.copy()
            
            for key in qs:
                value_list = qs[key]
                for i, value in enumerate(value_list):
                    if value.isdigit():
                        qs[key][i] = 'number'
                    else:
                        qs[key][i] = 'string'
            
            res += str(qs)
            
        return res
    
    def need_more_variants(self, reference):
        '''
        @return: True if there are not enough variants associated with
        this reference in the DB.
        '''
        clean_reference = self._clean_reference( reference )
        count = self._internal_dict.get( clean_reference, 0)
        if count >= MAX_VARIANTS:
            return False
        else:
            return True