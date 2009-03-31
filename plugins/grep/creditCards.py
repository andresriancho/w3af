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

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

import re


def luhnCheck(value):
    '''
    The Luhn check against the value which can be an array of digits, 
    numeric string or a positive integer.
    
    @author Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    '''
    # Prepare the value to be analyzed.
    arr = []
    for c in value:
        if c.isdigit():
            arr.append(int(c))
    arr.reverse()
    
    # Analyze
    for idx in [i for i in range(len(arr)) if i%2]:
        d = arr[idx] * 2
        if d > 9:
            d = d/10 + d % 10
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

        regex = '(?:^|[^\d])((?:<.*>)?\d{4}(?:</.*>)?[\- ]?(?:</.*>)?'
        regex += '\d{4}(?:</.*>)?[\- ]?(?:<.*>)?\d{2}(?:</.*>)?[\- ]?'
        regex += '(?:<.*>)?\d{2}(?:</.*>)?[\- ]?(?:<.*>)?\d{1,4}(?:</.*>)?)(?:[^\d]|$)'
        markupRegex = '(<.*?>)|(</.*?>)|\-'

        self._regex = re.compile(regex)
        self._markupRegex = re.compile(markupRegex)
        
    def grep(self, request, response):
        '''
        Plugin entry point, search for the credit cards.
        @return: None
        '''
        if response.is_text_or_html() and response.getCode() == 200:
            found_cards = self._find_card(response.getBody())
            for card in found_cards:
                v = vuln.vuln()
                v.setURL( response.getURL() )
                v.setId( response.id )
                v.setSeverity(severity.LOW)
                v.setName( 'Credit card number disclosure' )
                v.addToHighlight(card)
                msg = 'The URL: "' + v.getURL() + '" discloses the credit card number: "'
                msg += card + '".'
                v.setDesc( msg )
                kb.kb.append( self, 'creditCards', v )
     
    def _find_card(self, body):
        '''
        @return: A list of matching credit card numbers
        '''
        res = []

        matches = self._regex.findall(body)

        for possible_cc in matches:
            possible_cc = self._markupRegex.sub('', possible_cc)
            if luhnCheck(possible_cc):
                res.append(possible_cc)

        return res

    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        # Print results
        self.printUniq( kb.kb.getData( 'creditCards', 'creditCards' ), 'URL' )


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
        credit card numbers. It can be tested against the following URL:
            - https://www.paypal.com/en_US/vhelp/paypalmanager_help/credit_card_numbers.htm
        '''

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
 
