'''
ssn.py

Copyright 2008 Andres Riancho

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
import itertools

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
from core.data.bloomfilter.pybloom import ScalableBloomFilter

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity
from core.controllers.w3afException import w3afException
from .ssndata.ssnAreasGroups import areas_groups_map


class ssn(baseGrepPlugin):
    '''
    This plugin detects the occurence of US Social Security numbers in web pages.

    @author: dliz <dliz !at! users.sourceforge.net>
    '''
    # match numbers of the form: 'nnn-nn-nnnn', 'nnnnnnnnn', 'nnn nn nnnn'
    regex = '(?:^|[^\d])(\d{3})(?:[\- ]?)(\d{2})(?:[\- ]?)(\d{4})(?:[^\d]|$)'
    ssn_regex = re.compile(regex)
    

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        self._already_inspected = ScalableBloomFilter()
        self._ssnResponses = []
                
    def grep(self, request, response):
        '''
        Plugin entry point, find the SSN numbers.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None.

        >>> from core.data.url.httpResponse import httpResponse
        >>> from core.data.url.HTTPRequest import HTTPRequest
        >>> from core.data.parsers.urlParser import url_object
        
        Simple test, empty string.
        >>> body = ''
        >>> url = url_object('http://www.w3af.com/')
        >>> headers = {'content-type': 'text/html'}
        >>> response = httpResponse(200, body , headers, url, url)
        >>> request = HTTPRequest(url)
        >>> s = ssn(); s._already_inspected = set()
        >>> s.grep(request, response)
        >>> len(kb.kb.getData('ssn', 'ssn'))
        0

        With "-" separating the SSN parts
        >>> kb.kb.cleanup(); s._already_inspected = set()
        >>> body = 'header 771-12-9876 footer'
        >>> headers = {'content-type': 'text/html'}
        >>> response = httpResponse(200, body , headers, url, url)
        >>> s.grep(request, response)
        >>> len(kb.kb.getData('ssn', 'ssn'))
        1

        With HTML tags in the middle:
        >>> kb.kb.cleanup(); s._already_inspected = set()
        >>> body = 'header <b>771</b>-<b>12</b>-<b>9876</b> footer'
        >>> headers = {'content-type': 'text/html'}
        >>> response = httpResponse(200, body , headers, url, url)
        >>> s.grep(request, response)
        >>> len(kb.kb.getData('ssn', 'ssn'))
        1

        All the numbers together:
        >>> kb.kb.cleanup(); s._already_inspected = set()
        >>> body = 'header 771129876 footer'
        >>> headers = {'content-type': 'text/html'}
        >>> response = httpResponse(200, body , headers, url, url)
        >>> s.grep(request, response)
        >>> len(kb.kb.getData('ssn', 'ssn'))
        1

        One extra number at the end:
        >>> kb.kb.cleanup(); s._already_inspected = set()
        >>> body = 'header 7711298761 footer'
        >>> headers = {'content-type': 'text/html'}
        >>> response = httpResponse(200, body , headers, url, url)
        >>> s.grep(request, response)
        >>> len(kb.kb.getData('ssn', 'ssn'))
        0
        '''
        uri = response.getURI()
        if response.is_text_or_html() and response.getCode() == 200 and \
            response.getClearTextBody() is not None and \
            uri not in self._already_inspected:
            
            # Don't repeat URLs
            self._already_inspected.add(uri)
            found_ssn, validated_ssn = self._find_SSN(response.getClearTextBody())
            if validated_ssn:
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setURI( uri )
                v.setId( response.id )
                v.setSeverity(severity.LOW)
                v.setName( 'US Social Security Number disclosure' )
                msg = 'The URL: "' + uri + '" possibly discloses a US '
                msg += 'Social Security Number: "'+ validated_ssn +'"'
                v.setDesc( msg )
                v.addToHighlight( found_ssn )
                kb.kb.append( self, 'ssn', v )
     
    def _find_SSN(self, body_without_tags):
        '''
        @return: SSN as found in the text and SSN in its regular format if the body had an SSN

        >>> s = ssn()
        >>> s._find_SSN( '' )
        (None, None)
        >>> s._find_SSN( 'header 771129876 footer' )
        ('771129876', '771-12-9876')
        >>> s._find_SSN( '771129876' )
        ('771129876', '771-12-9876')
        >>> s._find_SSN( 'header 771 12 9876 footer' )
        ('771 12 9876', '771-12-9876')
        >>> s._find_SSN( 'header 771 12 9876 32 footer' )
        ('771 12 9876', '771-12-9876')
        >>> s._find_SSN( 'header 771 12 9876 32 64 footer' )
        ('771 12 9876', '771-12-9876')
        >>> s._find_SSN( 'header 771129876 771129875 footer' )
        ('771129876', '771-12-9876')
        '''
        validated_ssn = None
        ssn = None
        for match in self.ssn_regex.finditer(body_without_tags):
            validated_ssn = self._validate_SSN(match)
            if validated_ssn:
                ssn = match.group(0)
                ssn = ssn.strip()
                break

        return ssn, validated_ssn
    
    
    def _validate_SSN(self, potential_ssn):
        '''
        This method is called to validate the digits of the 9-digit number
        found, to confirm that it is a valid SSN. All the publicly available SSN
        checks are performed. The number is an SSN if: 
        1. the first three digits <= 772
        2. the number does not have all zeros in any digit group 3+2+4 i.e. 000-xx-####,
        ###-00-#### or ###-xx-0000 are not allowed
        3. the number does not start from 666-xx-####. 666 for area code is not allowed
        4. the number is not between 987-65-4320 to 987-65-4329. These are reserved for advts
        5. the number is not equal to 078-05-1120

        Source of information: wikipedia and socialsecurity.gov
        '''
        area_number = int(potential_ssn.group(1))
        group_number = int(potential_ssn.group(2))
        serial_number = int(potential_ssn.group(3))

        if not group_number:
            return False
        if not serial_number:
            return False

        group = areas_groups_map.get(area_number)        
        if not group:
            return False
        
        odd_one = xrange(1, 11, 2)
        even_two = xrange(10, 100, 2) # (10-98 even only)
        even_three = xrange(2, 10, 2)
        odd_four = xrange(11, 100, 2) # (11-99 odd only)
        le_group = lambda x: x <= group
        isSSN = False
    
        # For little odds (odds between 1 and 9)
        if group in odd_one:
            if group_number <= group:
                isSSN = True

        # For big evens (evens between 10 and 98)
        elif group in even_two:
            if group_number in itertools.chain(odd_one, 
                                               filter(le_group, even_two)):
                isSSN = True

        # For little evens (evens between 2 and 8)
        elif group in even_three:
            if group_number in itertools.chain(odd_one, even_two,
                                               filter(le_group, even_three)):
                isSSN = True

        # For big odds (odds between 11 and 99)
        elif group in odd_four:
            if group_number in itertools.chain(odd_one, even_two, even_three,
                                               filter(le_group, odd_four)):
                isSSN = True
        
        if isSSN:
            return '%s-%s-%s' % (area_number, group_number, serial_number)
        return None



    def end(self):
        '''
        This method is called when the plugin won't be used anymore.
        '''
        # Print results
        self.printUniq( kb.kb.getData( 'ssn', 'ssn' ), 'URL' )

    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol
        
    def setOptions(self, opt):
        pass
     
    def getLongDesc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugins scans every response page to find the strings that are likely to be 
        the US social security numbers. 
        '''
        
    def getPluginDeps(self):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return []
 
