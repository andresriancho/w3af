'''
feeds.py

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
from core.data.bloomfilter.bloomfilter import scalable_bloomfilter

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from lxml import etree


class feeds(baseGrepPlugin):
    '''
    Grep every page and finds rss, atom, opml feeds.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._feed_types = {'rss': 'RSS', # <rss version="...">
                            'feed': 'OPML',# <feed version="..."
                            'opml': 'OPML' # <opml version="...">
                           }
        self._already_inspected = scalable_bloomfilter()
        
        # Compile the XPATH
        self._tag_xpath = etree.XPath('//rss | //feed | //opml')
                
                
    def grep(self, request, response):
        '''
        Plugin entry point, find feeds.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        dom = response.getDOM()
        uri = response.getURI()
        
        # In some strange cases, we fail to normalize the document
        if uri not in self._already_inspected and dom is not None:

            self._already_inspected.add(uri)

            # Find all feed tags 
            element_list = self._tag_xpath(dom)
        
            for element in element_list:
                
                feed_tag = element.tag
                feed_type = self._feed_types[ feed_tag.lower() ]
                version = element.attrib.get('version', 'unknown')
                
                i = info.info()
                i.setPluginName(self.getName())
                i.setName(feed_type +' feed')
                i.setURI(uri)
                fmt = 'The URL "%s" is a %s version %s feed.'
                msg = fmt % (uri, feed_type, version) 
                i.setDesc( msg )
                i.setId( response.id )
                i.addToHighlight( feed_type )
                kb.kb.append( self, 'feeds', i )
    
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
        self.printUniq( kb.kb.getData( 'feeds', 'feeds' ), 'URL' )

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return []
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page and finds rss, atom, opml feeds on them. This may be usefull for 
        determining the feed generator and with that, the framework being used. Also this will be helpfull
        for testing feed injection.
        '''
