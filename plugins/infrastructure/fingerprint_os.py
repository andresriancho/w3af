'''
fingerprint_os.py

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
import core.data.kb.knowledge_base as kb
import core.data.kb.info as info

from core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from core.data.parsers.url import URL
from core.controllers.w3afException import w3afRunOnce
from core.controllers.misc.levenshtein import relative_distance_ge


class fingerprint_os(InfrastructurePlugin):
    '''
    Fingerprint the remote operating system using the HTTP protocol.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    
    def __init__(self):
        InfrastructurePlugin.__init__(self)
        
        self._exec = True
        
    def discover(self, fuzzable_request ):
        '''
        It calls the "main" and writes the results to the kb.
        
        @param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''
        if not self._exec:
            raise w3afRunOnce()
        
        self._exec = not self._find_OS(fuzzable_request)
    
    def _find_OS(self, fuzzable_request):
        '''
        Analyze responses and determine if remote web server runs on windows
        or *nix.
        
        @Return: None, the knowledge is saved in the knowledgeBase
        '''
        found_os = False
        freq_url = fuzzable_request.getURL() 
        filename = freq_url.getFileName()
        dirs = freq_url.getDirectories()[:-1] # Skipping "domain level" dir.
        
        if dirs and filename:
            
            last_url = dirs[-1]
            last_url = last_url.url_string
            
            windows_url = URL(last_url[0:-1] + '\\' + filename)
            windows_response = self._uri_opener.GET(windows_url)
            
            original_response = self._uri_opener.GET(freq_url)
            found_os = True

            if relative_distance_ge(original_response.getBody(),
                                    windows_response.getBody(), 0.98):
                i = info.info()
                i.setPluginName(self.get_name())
                i.set_name('Operating system')
                i.setURL( windows_response.getURL() )
                i.setMethod( 'GET' )
                i.set_desc('Fingerprinted this host as a Microsoft Windows system.' )
                i.set_id( [windows_response.id, original_response.id] )
                kb.kb.save( self, 'operating_system_str', 'windows' )
                kb.kb.append( self, 'operating_system', i )
                om.out.information( i.get_desc() )
            else:
                i = info.info()
                i.setPluginName(self.get_name())
                i.set_name('Operating system')
                i.setURL( original_response.getURL() )
                i.setMethod( 'GET' )
                msg = 'Fingerprinted this host as a *nix system. Detection for'
                msg += '  this operating system is weak, "if not windows: is linux".'
                i.set_desc( msg )
                i.set_id( [original_response.id, windows_response.id] )
                kb.kb.save( self, 'operating_system_str', 'unix' )
                kb.kb.append( self, 'operating_system', i )
                om.out.information( i.get_desc() )
        
        return found_os
    
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin fingerprints the remote web server and tries to determine the
        Operating System family (Windows, Unix, etc.).

        The fingerprinting is (at this moment) really trivial, because it only
        uses one technique: windows path separator in the URL. For example, if the
        input URL is http://host.tld/abc/def.html then the plugin verifies if the
        response for that resource and the http://host.tld/abc\\def.html is the same;
        which indicates that the server is running Windows.
        '''
