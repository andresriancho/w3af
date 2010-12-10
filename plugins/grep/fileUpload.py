'''
fileUpload.py

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
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
from core.data.bloomfilter.pybloom import ScalableBloomFilter
from core.data.options.optionList import optionList
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info


FILE_INPUT_XPATH = ".//input[translate(@type,'FILE','file')='file']"


class fileUpload(baseGrepPlugin):
    '''
    Find HTML forms with file upload capabilities.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        # Internal variables
        self._already_inspected = ScalableBloomFilter()

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
                for input_file in dom.xpath(FILE_INPUT_XPATH):
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName('File upload form')
                    i.setURL(url)
                    i.setId(response.id)
                    msg = 'The URL: "%s" has form with file upload ' \
                    'capabilities.' % url
                    i.setDesc(msg)
                    to_highlight = etree.tostring(input_file)
                    i.addToHighlight(to_highlight)
                    kb.kb.append(self, 'fileUpload', i)

    
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
        self.printUniq( kb.kb.getData( 'fileUpload', 'fileUpload' ), 'URL' )

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
        This plugin greps every page for forms with file upload capabilities.
        '''
