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

from lxml import etree

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
from core.data.db.temp_persist import disk_list
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.data.kb.knowledgeBase import kb
from core.data.kb.info import info

AUTOCOMPLETE_FORMS_XPATH = "//form[not(@autocomplete) or @autocomplete='on']"
PWD_INPUT_XPATH = "//input[translate(@type,'PASWORD','pasword')='password']"

class formAutocomplete(baseGrepPlugin):
    '''
    Grep every page for detection of forms with 'autocomplete' capabilities 
    containing password-type inputs.
      
    @author: Javier Andalia (jandalia@gmail.com)
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._already_inspected = disk_list()

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

        if response.is_text_or_html() and not url in self._already_inspected:

            self._already_inspected.append(url)
            dom = response.getDOM()

            if dom is not None:
                
                # Loop through "auto-completable" forms
                for form in dom.xpath(AUTOCOMPLETE_FORMS_XPATH):
                
                    # Test existance of password-type inputs
                    if form.xpath(PWD_INPUT_XPATH):
                        inf = info()
                        inf.setName('Auto-completable form')
                        inf.setURL(url)
                        inf.setId(response.id)
                        msg = 'The URL: "%s" has <form> element with ' \
                        'autocomplete capabilities.' % url
                        inf.setDesc(msg)
                        inf.addToHighlight(etree.tostring(form))
                        kb.append(self, 'formAutocomplete', inf)
                        # Enough with one input
                        break

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
        return '''
        This plugin greps every page for autocomplete-able forms containing
        password-type inputs.
        '''

    def getPluginDeps(self):
        '''
        @return: A list with the names of the plugins that should be runned
        before the current one.
        '''
        return []
