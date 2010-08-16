'''
ajax.py

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

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin

from core.data.getResponseType import *
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from core.data.db.temp_persist import disk_list

import re


class ajax(baseGrepPlugin):
    '''
    Grep every page for traces of Ajax code.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        # Internal variables
        self._already_inspected = disk_list()
        
        # Create the regular expression to search for AJAX
        ajax_regex_string = '(XMLHttpRequest|eval\(|ActiveXObject|Msxml2\.XMLHTTP|'
        ajax_regex_string += 'ActiveXObject|Microsoft\.XMLHTTP)'
        self._ajax_regex_re = re.compile( ajax_regex_string, re.IGNORECASE )

    def grep(self, request, response):
        '''
        Plugin entry point.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None, all results are saved in the kb.
        '''
        if response.is_text_or_html() and response.getURL() not in self._already_inspected:
            
            # Don't repeat URLs
            self._already_inspected.append( response.getURL() )
            
            soup = response.getSoup()
            # In some strange cases, BeautifulSoup can fail to normalize the document
            if soup != None:
                
                script_elements = soup.findAll('script')
                for element in script_elements:
                    # returns the text between <script> and </script>
                    script_content = element.string
                    
                    res = self._ajax_regex_re.search( script_content )
                    if res:
                        i = info.info()
                        i.setName('AJAX code')
                        i.setURL( response.getURL() )
                        i.setDesc( 'The URL: "' + i.getURL() + '" has a AJAX code.'  )
                        i.setId( response.id )
                        i.addToHighlight( res.group(0) )
                        kb.kb.append( self, 'ajax', i )
    
    def setOptions( self, OptionList ):
        pass
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol
        
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.printUniq( kb.kb.getData( 'ajax', 'ajax' ), 'URL' )

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
        This plugin greps every page for traces of Ajax code.
        '''
