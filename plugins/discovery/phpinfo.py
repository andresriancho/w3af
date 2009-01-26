'''
phpinfo.py

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

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import w3afException

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

import re


class phpinfo(baseDiscoveryPlugin):
    '''
    Search PHP Info file and if it finds it will determine the version of PHP.
    @author: Viktor Gazdag ( woodspeed@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._analyzed_dirs = []

    def discover(self, fuzzableRequest ):
        '''
        For every directory, fetch a list of files and analyze the response.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        
        new_fuzzable_requests = []

        is_404 = kb.kb.getData( 'error404page', '404' )
        for domain_path in urlParser.getDirectories(fuzzableRequest.getURL() ):

            if domain_path not in self._analyzed_dirs:

                # Save the domain_path so I know I'm not working in vane
                self._analyzed_dirs.append( domain_path )

                # Work!
                for php_info_filename in self._get_PHP_infofile():

                    # Request the file
                    php_info_url = urlParser.urlJoin(  domain_path , php_info_filename )
                    try:
                        response = self._urlOpener.GET( php_info_url, useCache=True )
                        om.out.debug( '[phpinfo] Testing "' + php_info_url + '".' )
                    except w3afException,  w3:
                        msg = 'Failed to GET phpinfo file: "' + php_info_url + '".'
                        msg += 'Exception: "' + str(w3) + '".'
                        om.out.debug( msg )
                    else:
                        # Check if it's a phpinfo file
                        if not is_404( response ):
                            
                            # Create the fuzzable request
                            new_fuzzable_requests.extend( self._createFuzzableRequests( response ) )
                            
                            regex_str = 'alt="PHP Logo" /></a><h1 class="p">PHP Version (.*?)</h1>'
                            php_version = re.search(regex_str, response.getBody(), re.IGNORECASE)
                            if php_version:
                                v = vuln.vuln()
                                v.setId( response.id )
                                v.setName( 'PHP Info file' )
                                v.setSeverity(severity.MEDIUM)
                                v.setURL( response.getURL() )
                                desc = 'The PHP Info file was found at: ' + v.getURL()
                                desc += ' and the version of PHP is: "' + php_version.group(1)
                                desc += '".'
                                v.setDesc( desc )
                                kb.kb.append( self, 'phpinfo', v )
                                om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
                                 
        return new_fuzzable_requests

    def _get_PHP_infofile( self ):
        '''
        @return: Filename of the php info file.
        '''
        res = []
        # TODO: If i'm scanning a windows system, do I really need to request case sensitive
        # filenames like phpversion and PHPversion ?
        res.extend( ['phpinfo.php' , 'test.php?mode=phpinfo' , 'PHPversion.php'] )
        res.extend( ['index.php?mode=phpinfo' , '?mode=phpinfo' , 'install.php?mode=phpinfo' ] )
        res.extend( ['admin.php?mode=phpinfo', 'info.php', 'phpversion.php', 'phpVersion.php'] )
        return res

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
        This plugin searches for the PHP Info file in all the directories and subdirectories that are sent as input
        and if it finds it will try to determine the version of the PHP. 
        The PHP Info file holds information about the PHP and the system (version, environment, modules, extensions,
        compilation options, etc). For example, if the input is:
            - http://localhost/w3af/index.php
            
        The plugin will perform these requests:
            - http://localhost/w3af/phpinfo.php
            - http://localhost/phpinfo.php
            - ...
            - http://localhost/test.php?mode=phpinfo
        '''
