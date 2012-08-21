'''
blank_body.py

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
from core.data.bloomfilter.bloomfilter import scalable_bloomfilter


class blank_body(GrepPlugin):
    '''
    Find responses with empty body.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        GrepPlugin.__init__(self)
        self._already_reported = scalable_bloomfilter()
        
    def grep(self, request, response):
        '''
        Plugin entry point, find the blank bodies and report them.

        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        if response.getBody() == '' and request.getMethod() in ['GET', 'POST']\
        and response.getCode() not in [401, 304, 302, 301, 204]\
        and 'location' not in response.getLowerCaseHeaders()\
        and response.getURL() not in self._already_reported:
            
            #   report these informations only once
            self._already_reported.add( response.getURL() )
            
            #   append the info object to the KB.
            i = info.info()
            i.setPluginName(self.getName())
            i.setName('Blank body')
            i.setURL( response.getURL() )
            i.setId( response.id )
            msg = 'The URL: "'+ response.getURL()  + '" returned an empty body. '
            msg += 'This could indicate an error.'
            i.setDesc(msg)
            kb.kb.append( self, 'blank_body', i )
        
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq( kb.kb.getData( 'blank_body', 'blank_body' ), None )
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds HTTP responses with a blank body, these responses may
        indicate errors or misconfigurations in the web application or the web
        server.
        '''
