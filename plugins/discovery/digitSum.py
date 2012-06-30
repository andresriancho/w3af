'''
digitSum.py

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

import re

from itertools import izip, repeat

import core.controllers.outputManager as om

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.w3afException import w3afException
from core.controllers.misc.levenshtein import relative_distance_lt
from core.controllers.coreHelpers.fingerprint_404 import is_404

from core.data.bloomfilter.bloomfilter import scalable_bloomfilter
from core.data.options.option import option
from core.data.options.optionList import optionList


class digitSum(baseDiscoveryPlugin):
    '''
    Take an URL with a number (index2.asp) and try to find related files (index1.asp, index3.asp).
    @author: Andres Riancho ( andres.riancho@gmail.com )  
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._already_visited = scalable_bloomfilter()
        
        # User options
        self._fuzz_images = False
        self._max_digit_sections = 4
        
    def discover(self, fuzzable_request ):
        '''
        Searches for new Url's by adding and substracting numbers to the url
        and the parameters.
        
        @parameter fuzzable_request: A fuzzableRequest instance that contains
                                     (among other things) the URL to test.
        '''
        self._fuzzable_requests = []
            
        url = fuzzable_request.getURL()
        headers = {'Referer': url.url_string }
                
        om.out.debug('digitSum is testing ' + fuzzable_request.getURL() )
        original_response = self._uri_opener.GET( fuzzable_request.getURL(),
                                                  cache=True, headers=headers )
        
        if original_response.is_text_or_html() or self._fuzz_images:
            
            fr_generator = self._mangle_digits( fuzzable_request )
            response_repeater = repeat(original_response)
            header_repeater = repeat(headers)
            
            args = izip(fr_generator, response_repeater, header_repeater)
            
            self._tm.threadpool.map_multi_args(self._do_request, args)
            
            # I add myself so the next call to this plugin wont find me ...
            # Example: index1.html ---> index2.html --!!--> index1.html
            self._already_visited.add( fuzzable_request.getURI() )
                
        return self._fuzzable_requests

    def _do_request(self, fuzzable_request, original_resp, headers):
        '''
        Send the request.
        
        @param fuzzable_request: The modified fuzzable request
        @param original_resp: The response for the original request that was
                              sent.
        '''
        response = self._uri_opener.GET(fuzzable_request.getURI(),
                                        cache=True,
                                        headers=headers)
        if not is_404( response ):
            # We have two different cases:
            #    - If the URLs are different, then there is nothing to think
            #      about, we simply found something new!
            #
            #    - If we changed the query string parameters, we have to check 
            #      the content
            if response.getURL() != original_resp.getURL() or \
            relative_distance_lt(response.getBody(),
                                 original_resp.getBody(), 0.7):
                self._fuzzable_requests.extend( self._createFuzzableRequests( response ) )
    
    def _mangle_digits(self, fuzzable_request):
        '''
        Mangle the digits (if any) in the fr URL.
        
        @param fuzzableRequest: The original fuzzableRequest
        @return: A generator which returns mangled fuzzable requests 
        '''
        # First i'll mangle the digits in the URL file
        filename = fuzzable_request.getURL().getFileName()
        domain_path = fuzzable_request.getURL().getDomainPath()
        for fname in self._do_combinations( filename ):
            fr_copy = fuzzable_request.copy()
            fr_copy.setURL( domain_path.urlJoin(fname) )
            
            if fr_copy.getURI() not in self._already_visited:
                self._already_visited.add( fr_copy.getURI() )
                
                yield fr_copy
        
        # Now i'll mangle the query string variables
        if fuzzable_request.getMethod() == 'GET':
            for parameter in fuzzable_request.getDc():
                
                # to support repeater parameter names...
                for element_index in xrange(len(fuzzable_request.getDc()[parameter])):
                    
                    combinations = self._do_combinations( fuzzable_request.getDc()
                                                          [ parameter ][element_index] )
                    for modified_value in fuzzable_request:
                        fr_copy = fuzzable_request.copy()
                        new_dc = fr_copy.getDc()
                        new_dc[ parameter ][ element_index ] = modified_value
                        fr_copy.setDc( new_dc )
                        if fr_copy.getURI() not in self._already_visited:
                            self._already_visited.add( fr_copy.getURI() )
                            
                            yield fr_copy
        
    def _do_combinations( self, a_string ):
        '''
        Example:
            - input: 'abc123'
            - output: ['abc122','abc124']
        
        Example:
            - input: 'abc123def01'
            - output: ['abc122def01','abc124def01','abc123def00','abc123def02']
        
        '''
        res = []
        splitted = self._find_digits( a_string )
        if len( splitted ) <= 2 * self._max_digit_sections:
            for i in xrange( len( splitted ) ):
                if splitted[ i ].isdigit():
                    splitted[ i ] = str( int(splitted[ i ]) + 1 )
                    res.append( ''.join(splitted) )
                    splitted[ i ] = str( int(splitted[ i ]) - 2 )
                    res.append( ''.join(splitted) )
                    splitted[ i ] = str( int(splitted[ i ]) + 1 )
                    
        return res
                
    def _find_digits( self, a_string ):
        '''
        Finds digits in a string and returns a list with string sections.
        For example:
            - input: 'foob45'
            - output: ['foo', '45']
            
        Another example:
            - input: 'f001bar112'
            - output: ['f', '00', 'bar', '112']
        
        @return: A list of strings.
        '''
        
        # regexes are soooooooooooooo cool !
        return [ x for x in re.split( r'(\d+)', a_string ) if x != '' ]
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = optionList()
        
        d = 'Apply URL fuzzing to all URLs, including images, videos, zip, etc.'
        h = 'It\'s safe to leave this option as the default.'
        o = option('fuzzImages', self._fuzz_images, d, 'boolean', help=h)
        ol.add(o)
        
        d = 'Set the top number of sections to fuzz'
        h = 'It\'s safe to leave this option as the default. For example, with maxDigitSections'
        h += ' = 1, this string wont be fuzzed: abc123def234 ; but this one will abc23ldd.'
        o = option('maxDigitSections', self._max_digit_sections, d, 'integer', help=h)
        ol.add(o)
                
        return ol
        
    def setOptions( self, optionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._fuzz_images = optionList['fuzzImages'].getValue()
        self._max_digit_sections = optionList['maxDigitSections'].getValue()
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin tries to find new URL's by changing the numbers that are
        present on it.
        
        Two configurable parameters exist:
            - fuzzImages
            - maxDigitSections
        
        An example will clarify what this plugin does, let's suppose that the
        input for this plugin is:
            - http://host.tld/index1.asp
            
        This plugin will request:
            - http://host.tld/index0.asp
            - http://host.tld/index2.asp
            
        If the response for the newly generated URL's is not an 404 error, then
        the new URL is a valid one that can contain more information and 
        injection points.      
        '''
