'''
creditCards.py

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
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
from core.data.getResponseType import *
import re
import core.data.constants.severity as severity


def luhnCheck(value):
    '''
    The Luhn check against the value which can be an array of digits, 
    numeric string or a positive integer.
    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    '''

    if type(value) == int:
        value = str(value)

    if type(value) == list:
        arr = value
    else:
        arr = []
        for c in value:
            arr.append(int(c))

    arr.reverse()
    even = False
    for idx in [i for i in range(len(arr)) if i%2]:
        d = arr[idx] * 2
        if d > 9:
            d = d/10 + d%10
        arr[idx] = d

    sm = sum(arr)
    return not (sm % 10)


class creditCards(baseGrepPlugin):
    '''
    This plugin detects the occurence of credit card numbers in web pages.

    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    '''
    

    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._cardResponses = []
        regex = '(?:^|[^\d])(\d{4}[\- ]?\d{4}[\- ]?\d{2}[\- ]?\d{2}[\- ]?\d{1,4})(?:[^\d]|$)'
        self._regex = re.compile(regex)
        
    def _testResponse(self, request, response):
        
        if isTextOrHtml(response.getHeaders()) and response.getCode()==200:
            if self._findCard(response.getBody()):
                v = vuln.vuln()
                v.setURL( response.getURL() )
                v.setId( response.id )
                v.setSeverity(severity.LOW)
                v.setName( 'Credit card number disclosure' )
                v.setDesc( "The URL: " + v.getURL() + " discloses credit card numbers." )
                kb.kb.append( self, 'creditCards', v )
     
    def _findCard(self, body):
        res = self._regex.search(body)
        return res and luhnCheck(res.group(1))
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        # Print results
        self.printUniq( kb.kb.getData( 'creditCards', 'creditCards' ), 'URL' )


    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/output.xsd
        '''
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
        </OptionList>\
        '
     
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugins scans every response page to find the strings that are likely to be 
        the credit card numbers. It can be tested against URL 
        https://www.paypal.com/en_US/vhelp/paypalmanager_help/credit_card_numbers.htm         
        '''
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
 
