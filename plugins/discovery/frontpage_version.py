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
#w3af modules
import core.controllers.outputManager as om
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.w3afException import w3afException, w3afRunOnce
import core.data.parsers.urlParser as urlParser

import core.data.kb.knowledgeBase as kb
from core.controllers.coreHelpers.fingerprint_404 import is_404
import core.data.kb.info as info

from core.data.bloomfilter.pybloom import ScalableBloomFilter

#python modules
import re


class frontpage_version(baseDiscoveryPlugin):
    '''
    Search FrontPage Server Info file and if it finds it will determine its version.
    @author: Viktor Gazdag ( woodspeed@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._analyzed_dirs = ScalableBloomFilter()
        self._exec = True

    def discover(self, fuzzableRequest ):
        '''
        For every directory, fetch a list of files and analyze the response.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        fuzzable_return_value = []
        
        if not self._exec:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
            
        else:
            # Run the plugin.
            self._exec = False

        for domain_path in urlParser.getDirectories(fuzzableRequest.getURL() ):

            if domain_path not in self._analyzed_dirs:

                # Save the domain_path so I know I'm not working in vane
                self._analyzed_dirs.add( domain_path )

                # Request the file
                frontpage_info_url = urlParser.urlJoin(  domain_path , "_vti_inf.html" )
                try:
                    response = self._urlOpener.GET( frontpage_info_url, useCache=True )
                    om.out.debug( '[frontpage_version] Testing "' + frontpage_info_url + '".' )
                except w3afException,  w3:
                    msg = 'Failed to GET Frontpage Server _vti_inf.html file: "'
                    msg += frontpage_info_url + '". Exception: "' + str(w3) + '".'
                    om.out.debug( msg )
                else:
                    # Check if it's a Fronpage Info file
                    if not is_404( response ):
                        fuzzable_return_value.extend( self._createFuzzableRequests( response ) )
                        self._analyze_response( response )
                        return fuzzable_return_value
                        
    def _analyze_response(self, response):
        '''
        It seems that we have found a _vti_inf file, parse it and analyze the content!
        
        @parameter response: The http response object for the _vti_inf file.
        @return: None. All the info is saved to the kb.
        '''
        regex_str = 'FPVersion="(.*?)"'
        regex_admin = 'FPAdminScriptUrl="(.*?)"'
        regex_author = 'FPAuthorScriptUrl="(.*?)"'
        
        #Get the Frontpage version
        frontpage_version_match = re.search(regex_str, response.getBody(), re.IGNORECASE)
        #Get the FPAdminScript url
        frontpage_admin = re.search(regex_admin, response.getBody(), re.IGNORECASE)
        #Get the FPAuthorScript url
        frontpage_author = re.search(regex_author, response.getBody(), re.IGNORECASE)
        
        if frontpage_version_match and frontpage_admin and frontpage_author:
            #Set the self._exec to false
            self._exec = False

            i = info.info()
            i.setPluginName(self.getName())
            i.setId( response.id )
            i.setName( 'FrontPage Configuration Information' )
            i.setURL( response.getURL() )
            desc = 'The FrontPage Configuration Information file was found at: "'
            desc += i.getURL() 
            desc += '" and the version of FrontPage Server Extensions is: "'
            desc += frontpage_version_match.group(1) + '". '
            i.setDesc( desc )
            i['version'] = frontpage_version_match.group(1)
            kb.kb.append( self, 'frontpage_version', i )
            om.out.information( i.getDesc() )

            #
            # Handle the admin.exe file
            #
            self._analyze_admin( response, frontpage_admin )

            #
            # Handle the author.exe file
            #
            self._analyze_author( response, frontpage_author )
            
        else:
            # This is wierd... we found a _vti_inf file, but there is no frontpage
            # information in it... IPS? WAF? honeypot?                            
            i = info.info()
            i.setPluginName(self.getName())
            i.setId( response.id )
            i.setName( 'Fake FrontPage Configuration Information' )
            i.setURL( response.getURL() )
            desc = 'A fake FrontPage Configuration Information file was found at: "'
            desc += i.getURL()
            desc += '". This may be an indication of a honeypot, a WAF or an IPS.'
            i.setDesc( desc )
            kb.kb.append( self, 'fake_frontpage', i )
            om.out.information( i.getDesc() )
    
    def _analyze_admin(self, response, frontpage_admin):
        '''
        Analyze the admin URL.
        
        @parameter response: The http response object for the _vti_inf file.
        @parameter frontpage_admin: A regex match object.
        @return: None. All the info is saved to the kb.
        '''
        i = info.info()
        i.setPluginName(self.getName())
        i.setId( response.id )
        i.setURL( response.getURL() )
        # Check for anomalies in the location of admin.exe
        if frontpage_admin.group(1) != '_vti_bin/_vti_adm/admin.exe':
            name = 'Uncommon FrontPage configuration'
            
            desc = 'The FPAdminScriptUrl is at: "'
            desc += frontpage_admin.group(1)
            desc += '" instead of the default location: "'
            desc += '_vti_bin/_vti_adm/admin.exe".'
        else:
            name = 'FrontPage FPAdminScriptUrl'

            desc = 'The FPAdminScriptUrl is at: "'
            desc += urlParser.getDomainPath(i.getURL())  + frontpage_admin.group(1)
            desc += '".'

        i.setName( name )
        i.setDesc( desc )
        i['FPAdminScriptUrl'] = frontpage_admin.group(1)
        kb.kb.append( self, 'frontpage_version', i )
        om.out.information( i.getDesc() )
            
    def _analyze_author(self, response, frontpage_author):
        '''
        Analyze the author URL.
        
        @parameter response: The http response object for the _vti_inf file.
        @parameter frontpage_author: A regex match object.
        @return: None. All the info is saved to the kb.
        '''
        i = info.info()
        i.setPluginName(self.getName())
        i.setId( response.id )
        i.setURL( response.getURL() )
        # Check for anomalies in the location of author.exe
        if frontpage_author.group(1) != '_vti_bin/_vti_aut/author.exe':
            name = 'Uncommon FrontPage configuration'
            
            desc = 'The FPAuthorScriptUrl is at: "'
            desc += frontpage_author.group(1)
            desc += '" instead of the default location: "'
            desc += '/_vti_bin/_vti_adm/author.exe".'
        else:
            name = 'FrontPage FPAuthorScriptUrl'

            desc = 'The FPAuthorScriptUrl is at: "'
            desc += urlParser.getDomainPath(i.getURL())  + frontpage_author.group(1)
            desc += '".'
            
        i.setName( name )
        i.setDesc( desc )
        i['FPAuthorScriptUrl'] = frontpage_author.group(1)
        kb.kb.append( self, 'frontpage_version', i )
        om.out.information( i.getDesc() )        

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass

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
        This plugin searches for the FrontPage Server Info file and if it finds it will try to
        determine the version of the Frontpage Server Extensions. The file is located inside the
        web server webroot. For example:
        
            - http://localhost/_vti_inf.html
        '''
