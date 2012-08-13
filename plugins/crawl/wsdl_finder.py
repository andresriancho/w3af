'''
wsdl_finder.py

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

from core.data.parsers.urlParser import url_object
from core.controllers.basePlugin.baseCrawlPlugin import baseCrawlPlugin
from core.controllers.w3afException import w3afException
from core.data.bloomfilter.bloomfilter import scalable_bloomfilter


class wsdl_finder(baseCrawlPlugin):
    '''
    Find web service definitions files.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    WSDL = ('?wsdl',
            '?WSDL')

    def __init__(self):
        baseCrawlPlugin.__init__(self)
        
        # Internal variables
        self._already_tested = scalable_bloomfilter()
        
    def crawl(self, fuzzableRequest ):
        '''
        If url not in _tested, append a ?WSDL and check the response.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains
                                    (among other things) the URL to test.
        '''
        url = fuzzableRequest.getURL().uri2url()
        url_string = url.url_string
        
        if url_string not in self._already_tested:
            self._already_tested.add( url_string )
            
            wsdl_url_generator = self.wsdl_url_generator(url_string)
            
            self._tm.threadpool.map(self._do_request, 
                                    wsdl_url_generator,
                                    chunksize=1)                
        return []

    def wsdl_url_generator( self, url_string ):
        for wsdl_parameter in self.WSDL:
            url_to_request = url_string + wsdl_parameter
            url_instance = url_object(url_to_request)
            yield url_instance
            
    def _do_request(self, url_to_request):
        '''
        Perform an HTTP request to the url_to_request parameter.
        @return: None.
        '''
        try:
            self._uri_opener.GET( url_to_request, cache=True )
        except w3afException:
            om.out.debug('Failed to request the WSDL file: ' + url_to_request)
        else:
            # The response is analyzed by the wsdlGreper plugin
            pass

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return ['grep.wsdl_greper']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds new web service descriptions and other web service 
        related files by appending "?WSDL" to all URL's and checking the response.
        '''
