'''
cross_domain_js.py

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
from core.data.bloomfilter.scalable_bloom import ScalableBloomFilter

SCRIPT_SRC_XPATH = ".//script[@src]"


class cross_domain_js(GrepPlugin):
    '''
    Find script tags with src attributes that point to a different domain. 
      
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        GrepPlugin.__init__(self)
        
        # Internal variables
        self._already_inspected = ScalableBloomFilter()
        self._script_src_xpath = etree.XPath( SCRIPT_SRC_XPATH )

    def grep(self, request, response):
        '''
        Plugin entry point, verify if the HTML has a form with file uploads.
        
        @param request: The HTTP request object.
        @param response: The HTTP response object
        @return: None
        '''
        url = response.getURL()

        if response.is_text_or_html() and not url in self._already_inspected:

            self._already_inspected.add(url)
            dom = response.getDOM()

            # In some strange cases, we fail to normalize the document
            if dom is not None:
                
                # Loop through script inputs tags                
                for script_src_tag in self._script_src_xpath( dom ):
                    
                    # This should be always False due to the XPATH we're using
                    # but you never know...
                    if not 'src' in script_src_tag.attrib:
                        continue
                    
                    script_src = script_src_tag.attrib['src']
                    script_full_url = response.getURL().urlJoin( script_src )
                    script_domain = script_full_url.getDomain()
                    
                    if script_domain != response.getURL().getDomain():
                        i = info.info()
                        i.set_plugin_name(self.get_name())
                        i.set_name('Cross-domain javascript source')
                        i.setURL(url)
                        i.set_id(response.id)
                        msg = 'The URL: "%s" has script tag with a source that points' \
                              ' to a third party site ("%s"). This practice is not' \
                              ' recommended as security of the current site is being' \
                              ' delegated to that entity.'
                        i.set_desc(msg)
                        to_highlight = etree.tostring(script_src_tag)
                        i.addToHighlight(to_highlight)
                        kb.kb.append(self, 'cross_domain_js', i)

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq( kb.kb.get( 'cross_domain_js', 'cross_domain_js' ), 'URL' )
    
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        Find script tags with src attributes that point to a different domain.
        
        It is important to notice that websites that depend on external javascript
        sources are delegating part of their security to those entities, so
        it is imperative to be aware of such code.
        '''
