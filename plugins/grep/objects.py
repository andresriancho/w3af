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
from lxml import etree

import core.data.kb.knowledge_base as kb
import core.data.kb.info as info

from core.controllers.plugins.grep_plugin import GrepPlugin
from core.data.bloomfilter.bloomfilter import scalable_bloomfilter


class objects(GrepPlugin):
    '''
    Grep every page for objects and applets.
      
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        GrepPlugin.__init__(self)
        
        # Compile the XPATH
        self._tag_xpath = etree.XPath('//object | //applet')
        self._tag_names = ('object', 'applet')
        self._already_analyzed = scalable_bloomfilter()
        

    def grep(self, request, response):
        '''
        Plugin entry point. Parse the object tags.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        url = response.getURL()
        dom = response.getDOM()
        
        if response.is_text_or_html() and dom is not None \
           and url not in self._already_analyzed:

            self._already_analyzed.add(url)
            
            elem_list = self._tag_xpath( dom )
            for element in elem_list:

                tag_name = element.tag
                
                i = info.info()
                i.setPluginName(self.get_name())
                i.set_name(tag_name.title() + ' tag')
                i.setURL(url)
                i.set_id( response.id )
                msg = 'The URL: "%s" has an "%s" tag. We recommend you download' \
                      ' the client side code and analyze it manually.'
                msg = msg % (i.getURI(), tag_name)
                i.set_desc( msg )
                i.addToHighlight( tag_name )

                kb.kb.append( self, tag_name, i )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        for obj_type in self._tag_names:
            self.print_uniq( kb.kb.get( 'objects', obj_type ), 'URL' )
                
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page for applets and other types of objects.
        '''
