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
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import re
from core.data.getResponseType import *

class feeds(baseGrepPlugin):
    '''
    Grep every page and finds rss, atom, opml feeds.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._compiledRegex = []
        
    def _getfeedsNames( self ):
        if not self._compiledRegex:
            self._compiledRegex.append( (re.compile('<rss version="(.*?)">'), 'RSS') )  # rss 0.9, rss 2.0
            self._compiledRegex.append( (re.compile('xmlns="http://purl.org/rss/(.*?)/"'), 'RSS') ) #rss 1.0
            self._compiledRegex.append( (re.compile('<feed version="(.*?)"'), 'OPML') )
            
        return self._compiledRegex
        
    def _testResponse(self, request, response):
        
        for regex, type in self._getfeedsNames():
            res = regex.search( response.getBody() )
            if res:
                resStr = res.groups()[0]
                i = info.info()
                i.setName(type +' feed')
                i.setURL( response.getURL() )
                i.setDesc( "The URL: " + i.getURL() + " is a " + type + " version " + resStr +" feed."  )
                i.setId( response.id )
                kb.kb.append( self, 'feeds', i )
    
    def setOptions( self, OptionList ):
        pass
    
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

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.printUniq( kb.kb.getData( 'feeds', 'feeds' ), 'URL' )

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
        This plugin greps every page and finds rss, atom, opml feeds on them. This may be usefull for 
        determining the feed generator and with that, the framework being used. Also this will be helpfull
        for testing feed injection.
        '''
