'''
file_upload.py

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

from lxml import etree

# options
from core.controllers.plugins.grep_plugin import GrepPlugin
from core.data.bloomfilter.bloomfilter import scalable_bloomfilter
from core.data.options.option_list import OptionList
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info


FILE_INPUT_XPATH = ".//input[translate(@type,'FILE','file')='file']"


class file_upload(GrepPlugin):
    '''
    Find HTML forms with file upload capabilities.
      
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        GrepPlugin.__init__(self)
        
        # Internal variables
        self._already_inspected = scalable_bloomfilter()
        self._file_input_xpath = etree.XPath( FILE_INPUT_XPATH )

    def grep(self, request, response):
        '''
        Plugin entry point, verify if the HTML has a form with file uploads.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        url = response.getURL()

        if response.is_text_or_html() and not url in self._already_inspected:

            self._already_inspected.add(url)
            dom = response.getDOM()

            # In some strange cases, we fail to normalize the document
            if dom is not None:

                # Loop through file inputs tags                
                for input_file in self._file_input_xpath( dom ):
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName('File upload form')
                    i.setURL(url)
                    i.set_id(response.id)
                    msg = 'The URL: "%s" has form with file upload ' \
                    'capabilities.' % url
                    i.setDesc(msg)
                    to_highlight = etree.tostring(input_file)
                    i.addToHighlight(to_highlight)
                    kb.kb.append(self, 'file_upload', i)

    
    def set_options( self, option_list ):
        pass
    
    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = OptionList()
        return ol

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq( kb.kb.get( 'file_upload', 'file_upload' ), 'URL' )

    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page for forms with file upload capabilities.
        '''
