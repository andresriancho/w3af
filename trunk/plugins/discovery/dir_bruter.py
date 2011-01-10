'''
dir_bruter.py

Copyright 2009 Jon Rose

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
from core.controllers.w3afException import w3afRunOnce
import core.data.parsers.urlParser as urlParser
import os

from core.controllers.coreHelpers.fingerprint_404 import is_404
from core.data.fuzzer.fuzzer import createRandAlNum


class dir_bruter(baseDiscoveryPlugin):
    '''
    Finds Web server directories by bruteforcing.

    @author: Jon Rose ( jrose@owasp.org )
    @author: Andres Riancho ( andres@bonsai-sec.com )
    '''
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._exec = True
        
        # User configured parameters
        self._dir_list = 'plugins' + os.path.sep + 'discovery' + os.path.sep + 'dir_bruter'
        self._dir_list += os.path.sep + 'common_dirs_small.db'
        self._be_recursive = True

        # Internal variables
        self._fuzzable_requests = []
        self._tested_base_url = False

    def discover(self, fuzzableRequest ):
        '''
        Get the file and parse it.
        @parameter fuzzableRequest: A fuzzableRequest instance that contains
                                                      (among other things) the URL to test.
        '''
        if not self._exec:
            raise w3afRunOnce()
        else:
            
            if not self._be_recursive:
                # Only run once
                self._exec = False

            self._fuzzable_requests = []
            
            domain_path = urlParser.getDomainPath( fuzzableRequest.getURL() )
            base_url = urlParser.baseUrl( fuzzableRequest.getURL() )
            
            to_test = []
            if not self._tested_base_url:
                to_test.append( base_url )
                self._tested_base_url = True
                
            if domain_path != base_url:
                to_test.append( domain_path )
            
            for base_path in to_test:
                
                #   Send the requests using threads:
                targs = ( base_path,  )
                self._tm.startFunction( target=self._bruteforce_directories, args=targs , ownerObj=self )
            
            # Wait for all threads to finish
            self._tm.join( self )

        return self._fuzzable_requests
    
    def _bruteforce_directories(self, base_path):
        '''
        @parameter base_path: The base path to use in the bruteforcing process, can be something
        like http://host.tld/ or http://host.tld/images/ .
        '''
        for directory_name in file(self._dir_list):
            directory_name = directory_name.strip()
            
            # ignore comments and empty lines
            if directory_name and not directory_name.startswith('#'):
                dir_url = urlParser.urlJoin(  base_path , directory_name)
                dir_url +=  '/'

                http_response = self._urlOpener.GET( dir_url, useCache=False )
                
                if not is_404( http_response ):
                    #
                    #   Looking fine... but lets see if this is a false positive or not...
                    #
                    dir_url = urlParser.urlJoin(  base_path , directory_name + createRandAlNum(5) )
                    dir_url +=  '/'
                    invalid_http_response = self._urlOpener.GET( dir_url, useCache=False )

                    if is_404( invalid_http_response ):
                        #
                        #   Good, the directory_name + createRandAlNum(5) return a 404, the original
                        #   directory_name is not a false positive.
                        #
                        fuzzable_reqs = self._createFuzzableRequests( http_response )
                        self._fuzzable_requests.extend( fuzzable_reqs )
                        
                        msg = 'Directory bruteforcer plugin found directory "'
                        msg += http_response.getURL()  + '"'
                        msg += ' with HTTP response code ' + str(http_response.getCode())
                        msg += ' and Content-Length: ' + str(len(http_response.getBody()))
                        msg += '.'
                        
                        om.out.information( msg )
            
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        d1 = 'Wordlist to use in directory bruteforcing process.'
        o1 = option('wordlist', self._dir_list , d1, 'string')
        
        d2 = 'If set to True, this plugin will bruteforce all directories, not only the root'
        d2 += ' directory.'
        o2 = option('be_recursive', self._be_recursive , d2, 'boolean')

        ol = optionList()
        ol.add(o1)
        ol.add(o2)

        return ol
        

    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        dir_list = OptionList['wordlist'].getValue()
        if os.path.exists( dir_list ):
            self._dir_list = dir_list
            
        self._be_recursive = OptionList['be_recursive'].getValue()

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
        This plugin finds directories on a web server by bruteforcing the names using a list.

        Two configurable parameters exist:
            - wordlist: The wordlist to be used in the directory bruteforce process.
            - be_recursive: If set to True, this plugin will bruteforce all directories, not only
            the root directory.
        '''
