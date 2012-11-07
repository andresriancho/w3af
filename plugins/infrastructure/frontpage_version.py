'''
frontpage_version.py

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

import core.controllers.outputManager as om
import core.data.kb.info as info
import core.data.kb.knowledge_base as kb

from core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from core.controllers.core_helpers.fingerprint_404 import is_404
from core.controllers.w3afException import w3afRunOnce
from core.controllers.w3afException import w3afException
from core.controllers.misc.decorators import runonce

from core.data.bloomfilter.bloomfilter import scalable_bloomfilter


class frontpage_version(InfrastructurePlugin):
    '''
    Search FrontPage Server Info file and if it finds it will determine its version.
    @author: Viktor Gazdag ( woodspeed@gmail.com )
    '''
    VERSION_RE = re.compile('FPVersion="(.*?)"', re.IGNORECASE)
    ADMIN_URL_RE = re.compile('FPAdminScriptUrl="(.*?)"', re.IGNORECASE )
    AUTHOR_URL_RE = re.compile('FPAuthorScriptUrl="(.*?)"', re.IGNORECASE )

    def __init__(self):
        InfrastructurePlugin.__init__(self)
        
        # Internal variables
        self._analyzed_dirs = scalable_bloomfilter()

    @runonce(exc_class=w3afRunOnce)
    def crawl(self, fuzzable_request ):
        '''
        For every directory, fetch a list of files and analyze the response.
        
        @parameter fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''
        for domain_path in fuzzable_request.getURL().getDirectories():

            if domain_path not in self._analyzed_dirs:

                # Save the domain_path so I know I'm not working in vane
                self._analyzed_dirs.add( domain_path )

                # Request the file
                frontpage_info_url = domain_path.urlJoin( "_vti_inf.html" )
                try:
                    response = self._uri_opener.GET( frontpage_info_url, cache=True )
                except w3afException,  w3:
                    msg = 'Failed to GET Frontpage Server _vti_inf.html file: "'
                    msg += frontpage_info_url + '". Exception: "' + str(w3) + '".'
                    om.out.debug( msg )
                else:
                    # Check if it's a Frontpage Info file
                    if not is_404( response ):
                        for fr in self._create_fuzzable_requests( response ):
                            self.output_queue.put(fr)
                        self._analyze_response( response )
                        
    def _analyze_response(self, response):
        '''
        It seems that we have found a _vti_inf file, parse it and analyze the content!
        
        @parameter response: The http response object for the _vti_inf file.
        @return: None. All the info is saved to the kb.
        '''
        version_mo = self.VERSION_RE.search( response.getBody() )
        admin_mo = self.ADMIN_URL_RE.search( response.getBody() )
        author_mo = self.AUTHOR_URL_RE.search( response.getBody() )
        
        if version_mo and admin_mo and author_mo:
            #Set the self._exec to false
            self._exec = False

            i = info.info()
            i.setPluginName(self.get_name())
            i.set_id( response.id )
            i.set_name( 'FrontPage Configuration Information' )
            i.setURL( response.getURL() )
            desc = 'The FrontPage Configuration Information file was found at: "'
            desc += i.getURL() 
            desc += '" and the version of FrontPage Server Extensions is: "'
            desc += version_mo.group(1) + '". '
            i.set_desc( desc )
            i['version'] = version_mo.group(1)
            kb.kb.append( self, 'frontpage_version', i )
            om.out.information( i.get_desc() )

            #
            # Handle the admin.exe file
            #
            self._analyze_admin( response, admin_mo )

            #
            # Handle the author.exe file
            #
            self._analyze_author( response, author_mo )
            
        else:
            # This is strange... we found a _vti_inf file, but there is no frontpage
            # information in it... IPS? WAF? honeypot?                            
            i = info.info()
            i.setPluginName(self.get_name())
            i.set_id( response.id )
            i.set_name( 'Fake FrontPage Configuration Information' )
            i.setURL( response.getURL() )
            desc = 'A fake FrontPage Configuration Information file was found at: "'
            desc += i.getURL()
            desc += '". This may be an indication of a honeypot, a WAF or an IPS.'
            i.set_desc( desc )
            kb.kb.append( self, 'fake_frontpage', i )
            om.out.information( i.get_desc() )
    
    def _analyze_admin(self, response, frontpage_admin):
        '''
        Analyze the admin URL.
        
        @parameter response: The http response object for the _vti_inf file.
        @parameter frontpage_admin: A regex match object.
        @return: None. All the info is saved to the kb.
        '''
        admin_location = response.getURL().getDomainPath().urlJoin(
                                           frontpage_admin.group(1) )
        i = info.info()
        i.setPluginName(self.get_name())
        i.set_id( response.id )
        i.setURL( admin_location )
        
        # Check for anomalies in the location of admin.exe
        if frontpage_admin.group(1) != '_vti_bin/_vti_adm/admin.exe':
            name = 'Uncommon FrontPage configuration'
            
            desc = 'The FPAdminScriptUrl is at: "'
            desc += admin_location
            desc += '" instead of the default location: "'
            desc += '_vti_bin/_vti_adm/admin.exe".'
        else:
            name = 'FrontPage FPAdminScriptUrl'

            desc = 'The FPAdminScriptUrl is at: "'
            desc += admin_location
            desc += '".'

        i.set_name( name )
        i.set_desc( desc )
        i['FPAdminScriptUrl'] = admin_location
        kb.kb.append( self, 'frontpage_version', i )
        om.out.information( i.get_desc() )
            
    def _analyze_author(self, response, frontpage_author):
        '''
        Analyze the author URL.
        
        @parameter response: The http response object for the _vti_inf file.
        @parameter frontpage_author: A regex match object.
        @return: None. All the info is saved to the kb.
        '''
        author_location = response.getURL().getDomainPath().urlJoin( 
                                            frontpage_author.group(1) )
        
        i = info.info()
        i.setPluginName(self.get_name())
        i.set_id( response.id )
        i.setURL( author_location )
        # Check for anomalies in the location of author.exe
        if frontpage_author.group(1) != '_vti_bin/_vti_aut/author.exe':
            name = 'Uncommon FrontPage configuration'
            
            desc = 'The FPAuthorScriptUrl is at: "'
            desc += author_location
            desc += '" instead of the default location: "'
            desc += '/_vti_bin/_vti_adm/author.exe".'
        else:
            name = 'FrontPage FPAuthorScriptUrl'

            desc = 'The FPAuthorScriptUrl is at: "'
            desc += author_location
            desc += '".'
            
        i.set_name( name )
        i.set_desc( desc )
        i['FPAuthorScriptUrl'] = author_location
        kb.kb.append( self, 'frontpage_version', i )
        om.out.information( i.get_desc() )        

    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin searches for the FrontPage Server Info file and if it finds
        it will try to determine the version of the Frontpage Server Extensions.
        The file is located inside the web server webroot. For example:
        
            - http://localhost/_vti_inf.html
        '''
