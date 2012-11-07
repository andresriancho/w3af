'''
oracle_discovery.py

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
import re

import core.data.kb.knowledge_base as kb
import core.data.kb.info as info
import core.controllers.outputManager as om

from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.w3afException import w3afRunOnce
from core.controllers.misc.decorators import runonce
from core.controllers.core_helpers.fingerprint_404 import is_404


class oracle_discovery(CrawlPlugin):
    '''
    Find Oracle applications on the remote web server.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    
    ORACLE_DATA = (
        # Example string:
        # <html><head><title>PPE is working</title></head><body>
        # PPE version 1.3.4 is working.</body></html>
        ('/portal/page', '<html><head><title>PPE is working</title></head>' +
                         '<body>(PPE) version (.*?) is working.</body></html>'),
        
        # Example strings:
        # Reports Servlet Omgevingsvariabelen 9.0.4.2.0
        # Reports Servlet Variables de Entorno 9.0.4.0.33
        ('/reports/rwservlet/showenv', '(Reports Servlet) [\w ]* ([\d\.]*)'),
    )
    
    ORACLE_DATA = ((url, re.compile(re_str)) for url, re_str in ORACLE_DATA)
    

    def __init__(self):
        CrawlPlugin.__init__(self)

    @runonce(exc_class=w3afRunOnce)
    def crawl(self, fuzzable_request ):
        '''
        GET some files and parse them.
        
        @parameter fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''
        base_url = fuzzable_request.getURL().baseUrl()
        
        for url, re_obj in self.ORACLE_DATA:

            oracle_discovery_URL = base_url.urlJoin( url )
            response = self._uri_opener.GET( oracle_discovery_URL, cache=True )
            
            if not is_404( response ):
                
                # Extract the links and send to core
                for fr in self._create_fuzzable_requests(response):
                    self.output_queue.put(fr)
                    
                mo = re_obj.search( response.getBody(), re.DOTALL)
                
                if mo:
                    i = info.info()
                    i.setPluginName(self.get_name())
                    i.set_name('Oracle application')
                    i.setURL( response.getURL() )
                    desc = '"%s" version "%s" was detected at "%s".'
                    desc = desc % (mo.group(1).title(), mo.group(2).title(),
                                   response.getURL())
                    i.set_desc(desc)
                    i.set_id( response.id )
                    kb.kb.append( self, 'oracle_discovery', i )
                    om.out.information( i.get_desc() )
                else:
                    msg = 'oracle_discovery found the URL: "%s" but failed to'\
                          ' parse it as an Oracle page. The first 50 bytes of'\
                          ' the response body is: "%s".'
                    body_start = response.getBody()[:50]
                    om.out.debug( msg % (response.getURL(), body_start))
    
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin retrieves Oracle Application Server URLs and extracts
        information available on them.
        '''
