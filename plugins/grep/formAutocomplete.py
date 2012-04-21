'''
formAutocomplete.py

Copyright 2010 Andres Riancho

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

from itertools import chain

from lxml import etree

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.controllers.outputManager as om
from core.data.bloomfilter.bloomfilter import scalable_bloomfilter
import core.data.kb.knowledgeBase as kb
from core.data.options.optionList import optionList
from core.data.kb.info import info

# Find all form elements that don't include the'autocomplete' attribute;
# otherwise (if included) not equals 'off'
AUTOCOMPLETE_FORMS_XPATH = ("//form[not(@autocomplete) or "
                            "translate(@autocomplete,'OF','of')!='off']")
# Find all input elements which type's lower-case value 
# equals-case-sensitive 'password'
PWD_INPUT_XPATH = "//input[translate(@type,'PASWORD','pasword')='password']"
# All 'text' input elements
TEXT_INPUT_XPATH = "//input[translate(@type,'TEXT','text')='text']"


class formAutocomplete(baseGrepPlugin):
    '''
    Grep every page for detection of forms with 'autocomplete' capabilities 
    containing password-type inputs.
      
    @author: Javier Andalia (jandalia =at= gmail.com)
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        # Internal variables
        self._already_inspected = scalable_bloomfilter()
        self._autocomplete_forms_xpath = etree.XPath( AUTOCOMPLETE_FORMS_XPATH )
        self._pwd_input_xpath = etree.XPath( PWD_INPUT_XPATH )
        self._text_input_xpath =  etree.XPath( TEXT_INPUT_XPATH )

    def grep(self, request, response):
        '''
        Plugin entry point, test existance of HTML auto-completable forms
        containing password-type inputs. Either form's <autocomplete> attribute
        is not present or is 'off'.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None, all results are saved in the kb.
        '''
        url = response.getURL()
        dom = response.getDOM()
        
        if response.is_text_or_html() and dom is not None \
        and not url in self._already_inspected:

            self._already_inspected.add(url)

            autocompletable = lambda inp: inp.get('autocomplete', 'on').lower() != 'off'

            # Loop through "auto-completable" forms
            for form in self._autocomplete_forms_xpath( dom ):

                passwd_inputs = self._pwd_input_xpath( form )

                # Test existence of password-type inputs and verify that
                # all inputs are autocompletable
                if passwd_inputs and all(map(autocompletable,
                chain(passwd_inputs, self._text_input_xpath(form) ))):
                    
                    i = info()
                    i.setName('Auto-completable form')
                    i.setURL(url)
                    i.setId(response.id)
                    msg = 'The URL: "%s" has a "<form>" element with ' \
                    'auto-complete enabled.' % url
                    i.setDesc(msg)
                    form_str = etree.tostring(form)
                    to_highlight = form_str[:(form_str).find('>') + 1]
                    i.addToHighlight(to_highlight)
                    
                    # Store and print
                    kb.kb.append(self, 'formAutocomplete', i)
                    om.out.information(msg)
                    
                    break


    def setOptions(self, OptionList):
        pass

    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = optionList()
        return ol

    def getLongDesc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return "This plugin greps every page for autocomplete-able forms " \
        "containing password-type inputs."

    def getPluginDeps(self):
        '''
        @return: A list with the names of the plugins that should be run
        before the current one.
        '''
        return []
