'''
meta_tags.py

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
import core.data.kb.knowledge_base as kb
import core.data.kb.info as info

from core.controllers.plugins.grep_plugin import GrepPlugin
from core.controllers.core_helpers.fingerprint_404 import is_404
from core.controllers.w3afException import w3afException
from core.data.bloomfilter.bloomfilter import scalable_bloomfilter


class meta_tags(GrepPlugin):
    '''
    Grep every page for interesting meta tags.
      
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    '''
    Can someone explain what this meta tag does?
    <meta name="verify-v1" content="/JBoXnwT1d7TbbWCwL8tXe+Ts2I2LXYrdnnK50g7kdY=" /> 
    
    Answer:
    That's one of the verification elements used by Google Sitemaps. When you sign up
    for Sitemaps you have to add that element to a root page to demonstrate to Google that
    you're the site owner. So there is probably a Sitemaps account for the site, if you 
    haven't found it already. 
    '''
    INTERESTING_WORDS = {'user':None, 'pass':None, 'microsoft':None,
                         'visual':None, 'linux':None, 'source':None,
                         'author':None, 'release':None,'version':None,
                         'verify-v1':'Google Sitemap' }

    def __init__(self):
        GrepPlugin.__init__(self)
        
        self._already_inspected = scalable_bloomfilter()
        
       
    def grep(self, request, response):
        '''
        Plugin entry point, search for meta tags.

        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        uri = response.getURI()
        
        if response.is_text_or_html() and not is_404( response ) \
        and uri not in self._already_inspected:

            self._already_inspected.add(uri)
            
            try:
                dp = dpCache.dpc.get_document_parser_for( response )
            except w3afException:
                pass
            else:
                meta_tag_list = dp.get_meta_tags()
                
                for tag in meta_tag_list:
                    tag_name = self._find_name( tag )
                    for attr in tag:
                        
                        key = attr[0].lower()
                        val = attr[1].lower()
                        
                        for word in self.INTERESTING_WORDS:

                            # Check if we have something interesting
                            # and WHERE that thing actually is
                            where = content = None
                            if ( word in key ):
                                where = 'name'
                                content = key
                            elif ( word in val ):
                                where = 'value'
                                content = val
                            
                            # Now... if we found something, report it =)
                            if where is not None:
                                # The atribute is interesting!
                                i = info.info()
                                i.setPluginName(self.get_name())
                                i.set_name('Interesting META tag')
                                i.setURI( response.getURI() )
                                i.set_id( response.id )
                                msg = 'The URI: "' +  i.getURI() + '" sent a META tag with '
                                msg += 'attribute '+ where +' "'+ content +'" which'
                                msg += ' looks interesting.'
                                i.addToHighlight( where, content )
                                if self.INTERESTING_WORDS.get(tag_name, None):
                                    msg += ' The tag is used for '
                                    msg += self.INTERESTING_WORDS[tag_name] + '.'
                                i.set_desc( msg )
                                kb.kb.append( self , 'meta_tags' , i )

    
    def _find_name( self, tag ):
        '''
        @return: the tag name.
        '''
        for attr in tag:
            if attr[0].lower() == 'name':
                return attr[1]
        return ''
        
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq( kb.kb.get( 'meta_tags', 'meta_tags' ), 'URL' )

    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page for interesting meta tags. Some interesting
        meta tags are the ones that contain : 'microsoft', 'visual', 'linux' .
        '''
