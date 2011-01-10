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

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.w3afException import w3afException
from core.controllers.misc.levenshtein import relative_distance_lt
import core.data.parsers.urlParser as urlParser

from core.data.bloomfilter.pybloom import ScalableBloomFilter

from core.controllers.coreHelpers.fingerprint_404 import is_404

import re


class digitSum(baseDiscoveryPlugin):
    '''
    Take an URL with a number ( index2.asp ) and try to find related files (index1.asp, index3.asp).
    @author: Andres Riancho ( andres.riancho@gmail.com )  
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._already_visited = ScalableBloomFilter()
        self._first_time = True
        
        # This is for the Referer
        self._headers = {}
        
        # User options
        self._fuzz_images = False
        self._max_digit_sections = 4
        
    def discover(self, fuzzableRequest ):
        '''
        Searches for new Url's by adding and substracting numbers to the url and the parameters.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        self._fuzzableRequests = []
            
        url = fuzzableRequest.getURL()
        self._headers = {'Referer':url}
        
        if self._first_time:
            self._first_time = False
        
        om.out.debug('digitSum is testing ' + fuzzableRequest.getURL() )
        original_response = self._urlOpener.GET( fuzzableRequest.getURL(), \
                                                            useCache=True, headers=self._headers )
        
        if original_response.is_text_or_html() or self._fuzz_images:
            for fr in self._mangle_digits( fuzzableRequest ):
                if fr.getURL() not in self._already_visited:
                    self._already_visited.add( fr.getURI() )
                    
                    targs = ( fr, original_response)
                    self._tm.startFunction( target=self._do_request, args=targs , ownerObj=self )
            
            # Wait for all threads to finish
            self._tm.join( self )
            
            # I add myself so the next call to this plugin wont find me ...
            # Example: index1.html ---> index2.html --!!--> index1.html
            self._already_visited.add( fuzzableRequest.getURI() )
                
        return self._fuzzableRequests

    def _do_request(self, fuzzableRequest, original_resp):
        '''
        Send the request.
        @parameter fuzzableRequest: The fuzzable request object to modify.
        @parameter original_resp: The response for the original request that was sent.
        '''
        try:
            response = self._urlOpener.GET(fuzzableRequest.getURI(), useCache=True,
                                                            headers=self._headers)
        except KeyboardInterrupt, e:
            raise e
        else:
            if not is_404( response ):
                # We have two different cases:
                # - If the URL's are different, then there is nothing to think about, we simply found
                # something new!
                #
                # - If we changed the query string parameters, we have to check the content
                is_new = False
                if response.getURL() != original_resp.getURL():
                    is_new = True
                elif relative_distance_lt(response.getBody(), original_resp.getBody(), 0.7):
                    is_new = True
                
                # Add it to the result.
                if is_new:
                    self._fuzzableRequests.extend( self._createFuzzableRequests( response ) )
                    om.out.debug('digitSum plugin found new URI: "' + fuzzableRequest.getURI() + '".')
    
    def _mangle_digits(self, fuzzableRequest):
        '''
        Mangle those digits.
        @param fuzzableRequest: The original fuzzableRequest
        @return: A list of fuzzableRequests.
        '''
        res = []
        # First i'll mangle the digits in the URL file
        filename = urlParser.getFileName( fuzzableRequest.getURL() )
        domain_path = urlParser.getDomainPath( fuzzableRequest.getURL() )
        for fname in self._do_combinations( filename ):
            fr_copy = fuzzableRequest.copy()
            fr_copy.setURL( domain_path + fname)
            res.append( fr_copy )
        
        # Now i'll mangle the query string variables
        if fuzzableRequest.getMethod() == 'GET':
            for parameter in fuzzableRequest.getDc():
                
                # to support repeater parameter names...
                for element_index in xrange(len(fuzzableRequest.getDc()[parameter])):
                    
                    for modified_value in self._do_combinations( fuzzableRequest.getDc()[ parameter ][element_index] ):
                        fr_copy = fuzzableRequest.copy()
                        new_dc = fr_copy.getDc()
                        new_dc[ parameter ][ element_index ] = modified_value
                        fr_copy.setDc( new_dc )
                        res.append( fr_copy )
        
        return res
        
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
        d1 = 'Apply URL fuzzing to all URLs, including images, videos, zip, etc.'
        h1 = 'It\'s safe to leave this option as the default.'
        o1 = option('fuzzImages', self._fuzz_images, d1, 'boolean', help=h1)
        
        d2 = 'Set the top number of sections to fuzz'
        h2 = 'It\'s safe to leave this option as the default. For example, with maxDigitSections'
        h2 += ' = 1, this string wont be fuzzed: abc123def234 ; but this one will abc23ldd.'
        o2 = option('maxDigitSections', self._max_digit_sections, d2, 'integer', help=h2)

        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        return ol
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._fuzz_images = optionsMap['fuzzImages'].getValue()
        self._max_digit_sections = optionsMap['maxDigitSections'].getValue()
    
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin tries to find new URL's by changing the numbers that are present on it.
        
        Two configurable parameters exist:
            - fuzzImages
            - maxDigitSections
        
        An example will clarify what this plugin does, let's suppose that the input for this plugin is:
            - http://host.tld/index1.asp
            
        This plugin will request:
            - http://host.tld/index0.asp
            - http://host.tld/index2.asp
            
        If the response for the newly generated URL's is not an 404 error, then the new URL is a valid one that
        can contain more information and injection points.      
        '''
