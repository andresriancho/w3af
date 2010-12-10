'''
metaTags.py

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

import core.data.parsers.dpCache as dpCache
import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
from core.data.bloomfilter.pybloom import ScalableBloomFilter

from core.controllers.coreHelpers.fingerprint_404 import is_404
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from core.controllers.w3afException import w3afException


class metaTags(baseGrepPlugin):
    '''
    Grep every page for interesting meta tags.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        self._comments = {}
        self._search404 = False
        
        self._interesting_words = {'user':None, 'pass':None, 'microsoft':None,
        'visual':None, 'linux':None, 'source':None, 'author':None, 'release':None,
        'version':None, 'verify-v1':'Google Sitemap' }
        self._already_inspected = ScalableBloomFilter()
        
        '''
        Can someone explain what this meta tag does?
        <meta name="verify-v1" content="/JBoXnwT1d7TbbWCwL8tXe+Ts2I2LXYrdnnK50g7kdY=" /> 
        
        Answer:
        That's one of the verification elements used by Google Sitemaps. When you sign up
        for Sitemaps you have to add that element to a root page to demonstrate to Google that
        you're the site owner. So there is probably a Sitemaps account for the site, if you 
        haven't found it already. 
        '''
        
    def grep(self, request, response):
        '''
        Plugin entry point, search for meta tags.

        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        uri = response.getURI()
        
        if response.is_text_or_html() and not is_404( response ) and \
            uri not in self._already_inspected:

            self._already_inspected.add(uri)
            
            try:
                dp = dpCache.dpc.getDocumentParserFor( response )
            except w3afException:
                pass
            else:
                meta_tag_list = dp.getMetaTags()
                
                for tag in meta_tag_list:
                    name = self._find_name( tag )
                    for attr in tag:
                        for word in self._interesting_words:

                            # Check if we have something interesting
                            # and WHERE that thing actually is
                            where = value = None
                            if ( word in attr[0].lower() ):
                                where = 'name'
                                value = attr[0].lower()
                            elif ( word in attr[1].lower() ):
                                where = 'value'
                                value = attr[1].lower()
                            
                            # Now... if we found something, report it =)
                            if where:
                                # The atribute is interesting!
                                i = info.info()
                                i.setPluginName(self.getName())
                                i.setName('Interesting META tag')
                                i.setURI( response.getURI() )
                                i.setId( response.id )
                                msg = 'The URI: "' +  i.getURI() + '" sent a META tag with '
                                msg += 'attribute '+ where +' "'+ value +'" which'
                                msg += ' looks interesting.'
                                i.addToHighlight( where, value )
                                if self._interesting_words.get(name, None):
                                    msg += ' The tag is used for '
                                    msg += self._interesting_words[name] + '.'
                                i.setDesc( msg )
                                kb.kb.append( self , 'metaTags' , i )

                            else:
                                # The attribute is not interesting
                                pass
    
    def _find_name( self, tag ):
        '''
        @return: the tag name.
        '''
        for attr in tag:
            if attr[0].lower() == 'name':
                return attr[1]
        return ''
        
    def setOptions( self, optionsMap ):
        self._search404 = optionsMap['search404'].getValue()
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Search for meta tags in 404 pages.'
        o1 = option('search404', self._search404, d1, 'boolean')
        
        ol = optionList()
        ol.add(o1)
        return ol
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        # Now print the information objects
        self.printUniq( kb.kb.getData( 'metaTags', 'metaTags' ), 'URL' )

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
        This plugin greps every page for interesting meta tags. Some interesting meta tags are the ones
        that contain : 'microsoft', 'visual', 'linux' .
        '''
