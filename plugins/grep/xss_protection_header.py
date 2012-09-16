'''
xss_protection_header.py

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
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from core.controllers.plugins.grep_plugin import GrepPlugin


class xss_protection_header(GrepPlugin):
    '''
    Grep headers for "X-XSS-Protection: 0" which disables security features in
    the browser.
      
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    def __init__(self):
        GrepPlugin.__init__(self)

    def grep(self, request, response):
        '''
        Plugin entry point.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None, all results are saved in the kb.
        '''
        value = response.getLowerCaseHeaders().get('x-xss-protection', None)
        if value == '0':
            i = info.info()
            i.setPluginName(self.getName())
            i.setName('Insecure X-XSS-Protection header usage')
            i.setURL( response.getURL() )
            i.set_id( response.id )
            msg = 'The remote web server sent the HTTP X-XSS-Protection header'\
                  ' with a 0 value, which disables Internet Explorer\'s XSS ' \
                  ' filter. In most cases, this is a bad practice and should' \
                  ' be subject to review.'
            i.setDesc( msg )
            i.addToHighlight( 'X-XSS-Protection' )
            kb.kb.append( self , 'xss_protection_header' , i )

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq( kb.kb.get( 'xss_protection_header', 
                                    'xss_protection_header' ), 'URL' )
            
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin detects insecure usage of the "X-XSS-Protection" header as
        explained in the MSDN blog article "Controlling the XSS Filter".
        '''
