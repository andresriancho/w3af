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


import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
from core.data.getResponseType import *
import re
import core.data.constants.severity as severity

class ssn(baseGrepPlugin):
    '''
    This plugin detects the occurence of US Social Security numbers in web pages.

    @author: dliz <dliz !at! users.sourceforge.net>
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._ssnResponses = []
        # match numbers of the form: 'nnn-nn-nnnn', 'nnnnnnnnn', 'nnn nn nnnn'
        regex = '(?:^|[^\d])(\d{3})(?:[\- ]?)(\d{2})(?:[\- ]?)(\d{4})(?:[^\d]|$)'
        self._regex = re.compile(regex)
        # re that removes tags
        self._re_removeTags = re.compile('(<.*?>|</.*?>)')
        
    def _testResponse(self, request, response):
        if response.is_text_or_html() and response.getCode() == 200:
            found_ssn = self._findSsn(response.getBody())
            if found_ssn:
                v = vuln.vuln()
                v.setURL( response.getURL() )
                v.setId( response.id )
                v.setSeverity(severity.LOW)
                v.setName( 'US Social Security Number disclosure' )
                v.setDesc( 'The URL: "' + v.getURL() + '" possibly discloses a US Social Security Number: "'+ found_ssn +'"' )
                kb.kb.append( self, 'ssn', v )
     
    def _findSsn(self, body):
        # Now, remove html tags
        bodyWithoutTags = self._re_removeTags.sub('', body)
        validate_res = False
        lines = str(bodyWithoutTags).split('\n')
        for line in lines:
            res = self._regex.search(str(line))
            if (res != None):
                validate_res = self._validSsn(res)
                if validate_res:
                    break
        return validate_res
    
    def _validSsn(self, potential_ssn):
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
       area_code        = int(potential_ssn.group(1))
       group_number     = int(potential_ssn.group(2))
       serial_number    = int(potential_ssn.group(3))
       '''Checks'''
       if ((area_code > 772) or (area_code == 0) or (area_code == 666)):
            om.out.debug("area_code erred out: " + str(area_code) )
            return False
       if (group_number == 0):
            om.out.debug("group_number erred out: "+ str( group_number) )
            return False
       if (serial_number == 0):
            om.out.debug("serial_number erred out: "+ str(serial_number))
            return False
       if ((area_code == 987) and (group_number == 65) and ((4320 <= serial_number) or (serial_number <= 4329))):
            om.out.debug("advt area code erred out: " + str(area_code) + ' ' +str(group_number) + ' ' +str(serial_number) )
            return False
       if ((area_code == 78) and (group_number == 5) and (serial_number == 1120)):
            om.out.debug("invalid ssn erred out: "+ str(area_code)  + ' ' + str(group_number) + ' ' + str(serial_number) )
            return False
       
       # If none of above conditions, then we have a valid ssn in the document. And we return it
       return str(area_code)+'-'+ str(group_number)+ '-' + str(serial_number)


    def end(self):
        '''
        This method is called when the plugin won't be used anymore.
        '''
        # Print results
        self.printUniq( kb.kb.getData( 'ssn', 'ssn' ), 'URL' )


    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol
        
    def setOptions( self, opt ):
        pass
     
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugins scans every response page to find the strings that are likely to be 
        the US social security numbers. 
        '''
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return []
 
