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

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

import re

class feeds(baseGrepPlugin):
    '''
    Grep every page and finds rss, atom, opml feeds.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._compiledRegex = []
        
    def _get_feeds( self ):
        if not self._compiledRegex:
            # rss 0.9, rss 2.0
            self._compiledRegex.append( (re.compile('<rss version="(.*?)">', re.IGNORECASE), 'RSS') )
            # rss 1.0
            self._compiledRegex.append( (re.compile('xmlns="http://purl.org/rss/(.*?)/"', re.IGNORECASE), 'RSS') )
            # OPML
            self._compiledRegex.append( (re.compile('<feed version="(.*?)"', re.IGNORECASE), 'OPML') )
            self._compiledRegex.append( (re.compile('<opml version="(.*?)">', re.IGNORECASE), 'OPML') )
            
        return self._compiledRegex
        
    def grep(self, request, response):
        '''
        Plugin entry point, find feeds.
        @return: None
        '''

        # Performance enhancement
        # (this was the longer string I could find that intersecter all the feed strings)
        if '="' in response.getBody():

            # Now do the real work
            for regex, feed_type in self._get_feeds():
                match = regex.search( response.getBody() )
                if match:
                    match_string = match.groups()[0]
                    i = info.info()
                    i.setName(feed_type +' feed')
                    i.setURL( response.getURL() )
                    msg = 'The URL: "' + i.getURL() + '" is a ' + feed_type + ' version "' 
                    msg += match_string + '" feed.'
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
