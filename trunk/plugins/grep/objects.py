'''
objects.py

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

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from core.data.bloomfilter.pybloom import ScalableBloomFilter


class objects(baseGrepPlugin):
    '''
    Grep every page for objects and applets.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        self._tag_names = []
        self._tag_names.append('object')
        self._tag_names.append('applet')
        
        self._already_analyzed = ScalableBloomFilter()

    def grep(self, request, response):
        '''
        Plugin entry point. Parse the object tags.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        url = response.getURL()
        if response.is_text_or_html() and url not in self._already_analyzed:

            self._already_analyzed.add(url)
            
            dom = response.getDOM()

            # In some strange cases, we fail to normalize the document
            if dom is not None:
            
                for tag_name in self._tag_names:
                    
                    # Find all input tags with a type file attribute
                    element_list = dom.xpath('//%s' % tag_name )
                    
                    if element_list:
                        i = info.info()
                        i.setPluginName(self.getName())
                        i.setName(tag_name.title() + ' tag')
                        i.setURL(url)
                        i.setId( response.id )
                        i.setDesc( 'The URL: "' + i.getURL() + '" has an '+ tag_name + ' tag.' )          
                        i.addToHighlight( tag_name )

                        kb.kb.append( self, tag_name, i )
    
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
        # Print objects
        self.printUniq( kb.kb.getData( 'objects', 'object' ), 'URL' )
        
        # Print applets
        self.printUniq( kb.kb.getData( 'objects', 'applet' ), 'URL' )
        
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
        This plugin greps every page for applets and other types of objects.
        '''
