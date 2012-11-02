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
import os

from itertools import repeat, izip

import core.controllers.outputManager as om

from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.w3afException import w3afRunOnce
from core.controllers.core_helpers.fingerprint_404 import is_404

from core.data.options.opt_factory import opt_factory
from core.data.options.option_types import INPUT_FILE, BOOL
from core.data.options.option_list import OptionList
from core.data.fuzzer.fuzzer import rand_alnum
from core.data.db.disk_set import disk_set


class dir_bruter(CrawlPlugin):
    '''
    Finds Web server directories by bruteforcing.

    @author: Jon Rose ( jrose@owasp.org )
    @author: Andres Riancho ( andres@bonsai-sec.com )
    '''
    def __init__(self):
        CrawlPlugin.__init__(self)
        
        # User configured parameters
        self._dir_list = os.path.join('plugins','crawl', 'dir_bruter', 
                                      'common_dirs_small.db')
        self._be_recursive = True

        # Internal variables
        self._exec = True
        self._already_tested = disk_set()

    def crawl(self, fuzzable_request ):
        '''
        Get the file and parse it.
        
        @param fuzzable_request: A fuzzable_request instance that contains
                               (among other things) the URL to test.
        '''
        if not self._exec:
            raise w3afRunOnce()
        else:
            domain_path = fuzzable_request.getURL().getDomainPath()
            base_url = fuzzable_request.getURL().baseUrl()
            
            if not self._be_recursive:
                # Only run once
                self._exec = False

                if base_url not in self._already_tested:
                    self._already_tested.add( base_url )
                    self._bruteforce_directories( base_url )
                
            elif domain_path not in self._already_tested:
                self._already_tested.add( domain_path )
                self._bruteforce_directories( domain_path )

    def _dir_name_generator(self, base_path):
        '''
        Simple generator that returns the names of the directories to test. It
        extracts the information from the user configured wordlist parameter.
        
        @yields: (A string with the directory name, a URL object with the dir name) 
        '''
        for directory_name in file(self._dir_list):
            directory_name = directory_name.strip()
            
            # ignore comments and empty lines
            if directory_name and not directory_name.startswith('#'):
                dir_url = base_path.urlJoin( directory_name +  '/' )
                yield directory_name, dir_url
    
    def _send_and_check(self, base_path, (directory_name, dir_url) ):
        '''
        Performs a GET and verifies that the response is not a 404.
        
        @return: None, data is stored in self.output_queue 
        '''
        try:
            http_response = self._uri_opener.GET( dir_url, cache=False )
        except:
            pass
        else:
            if not is_404( http_response ):
                #
                #   Looking fine... but lets see if this is a false positive or not...
                #
                dir_url = base_path.urlJoin( directory_name + rand_alnum(5) + '/')
    
                invalid_http_response = self._uri_opener.GET( dir_url, cache=False )
    
                if is_404( invalid_http_response ):
                    #
                    #    Good, the directory_name + rand_alnum(5) return a
                    #    404, the original directory_name is not a false positive.
                    #
                    for fr in self._create_fuzzable_requests( http_response ):
                        self.output_queue.put(fr)
                    
                    msg = 'Directory bruteforcer plugin found directory "'
                    msg += http_response.getURL()  + '"'
                    msg += ' with HTTP response code ' + str(http_response.getCode())
                    msg += ' and Content-Length: ' + str(len(http_response.getBody()))
                    msg += '.'
                    
                    om.out.information( msg )
    
    def _bruteforce_directories(self, base_path):
        '''
        @param base_path: The base path to use in the bruteforcing process,
                          can be something like http://host.tld/ or
                          http://host.tld/images/ .
                          
        @return: None, the data is stored in self.output_queue
        '''
        dir_name_generator = self._dir_name_generator(base_path)
        base_path_repeater = repeat(base_path)
        arg_iter = izip(base_path_repeater, dir_name_generator)
        
        self._tm.threadpool.map_multi_args(self._send_and_check, arg_iter,
                                           chunksize=20)

            
    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = OptionList()
            
        d = 'Wordlist to use in directory bruteforcing process.'
        o = opt_factory('wordlist', self._dir_list , d, INPUT_FILE)
        ol.add(o)
        
        d = 'If set to True, this plugin will bruteforce all directories, not only the root'
        d += ' directory.'
        h = 'WARNING: Enabling this will make the plugin send LOTS of requests.'
        o = opt_factory('be_recursive', self._be_recursive , d, BOOL, help=h)
        ol.add(o)
        
        return ol
        

    def set_options( self, option_list ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of get_options().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._dir_list = option_list['wordlist'].get_value()
        self._be_recursive = option_list['be_recursive'].get_value()

    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds directories on a web server by brute-forcing their
        names using a wordlist.
        
        Given the large amount of time that this plugin can consume, by default,
        it will only try to identify directories in the web root ("/"), ignoring
        the path that is sent as its input.

        Two configurable parameters exist:
            - wordlist: The wordlist to be used in the directory bruteforce process.
            - be_recursive: If set to True, this plugin will bruteforce all 
                            directories, not only the root directory.
        '''
