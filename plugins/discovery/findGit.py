'''
findGit.py

Copyright 2010 Adam Baldwin

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
import StringIO

import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.data.db.disk_set import disk_set

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.w3afException import w3afException
from core.controllers.coreHelpers.fingerprint_404 import is_404


class findGit(baseDiscoveryPlugin):
    '''
    Find GIT repositories
    @author: Adam Baldwin (adam_baldwin@ngenuity-is.com)
    '''
    
    COMPILED_GIT_INFO = []
    # Don't change the order! the first element is used in a different way
    COMPILED_GIT_INFO.append( ['.git/HEAD',re.compile('^ref: refs/')])
    COMPILED_GIT_INFO.append( ['.git/info/refs',re.compile('^[a-f0-9]{40}\s+refs/')])
    COMPILED_GIT_INFO.append( ['.git/objects/info/packs',re.compile('^P pack-[a-f0-9]{40}\.pack')])
    COMPILED_GIT_INFO.append( ['.git/packed-refs',re.compile('^[a-f0-9]{40} refs/')])
    COMPILED_GIT_INFO.append( ['.git/refs/heads/master',re.compile('^[a-f0-9]{40}')])
    
    
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._analyzed_dirs = disk_set()
        self._fuzzable_requests_to_return = []

    def discover(self, fuzzableRequest ):
        '''
        For every directory, fetch a list of files and analyze the response
        using regex.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains
                                    (among other things) the URL to test.
        '''
        domain_path = fuzzableRequest.getURL().getDomainPath()
        self._fuzzable_requests_to_return = []
        
        if domain_path not in self._analyzed_dirs:
            self._analyzed_dirs.add( domain_path )

            #
            #   First we check if the .git/HEAD file exists
            #
            relative_url, reg_ex = self.COMPILED_GIT_INFO[0]
            git_url = domain_path.urlJoin(relative_url)
            if self._check_if_exists(domain_path, git_url, reg_ex):
                #
                #   It looks like we have a GIT repository!
                #
                requests_args = []
                
                for relative_url, reg_ex in self.COMPILED_GIT_INFO[1:]:
                    git_url = domain_path.urlJoin(relative_url)
                    requests_args.append( (domain_path, git_url, reg_ex) )
                
                # Send all requests, block until all are done
                self._tm.threadpool.map_multi_args(self._check_if_exists, requests_args)
                                
        return self._fuzzable_requests_to_return
    
    def _check_if_exists(self, domain_path, git_url, regular_expression):
        '''
        Check if the file exists and if it matches the regular expression.
        
        @param git_file_url: The URL to check
        @param domain_path: The original domain and path
        @param regular_expression: The regex that verifies that this is a GIT repo
        
        @return: True if the file exists and matches the regex
        '''
        try:
            response = self._uri_opener.GET( git_url, cache=True )
        except w3afException:
            om.out.debug('Failed to GET git file:' + git_url)
        else:
            if not is_404(response):
                # Check pattern
                f = StringIO.StringIO(response.getBody())
                for line in f:
                    if regular_expression.match(line):
                        v = vuln.vuln()
                        v.setPluginName(self.getName())
                        v.setId( response.id )
                        v.setName( 'Possible Git repository found' )
                        v.setSeverity(severity.LOW)
                        v.setURL( response.getURL() )
                        
                        msg = 'A Git repository file was found at: "' + v.getURL() + '" ; this could'
                        msg += ' indicate that a Git repo is accessible. You might be able to download'
                        msg += ' the Web application source code by running'
                        msg += ' "git clone ' + domain_path + '"'
                        v.setDesc( msg )
                        
                        om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
                        
                        kb.kb.append( self, 'GIT', v )
                        
                        fuzzable_requests = self._createFuzzableRequests( response )
                        self._fuzzable_requests_to_return.extend( fuzzable_requests )
                        
                        return True
        
        return False
                    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
    	This plugin search for evidence of Git metadata in a directory. 
        For example, if the input is:
            - http://host.tld/w3af/index.php
            
        The plugin will perform a request to:
            - http://host.tld/w3af/.git/HEAD

        And then, if the response was not a 404:
            - http://host.tld/w3af/.git/info/refs
            - http://host.tld/w3af/.git/packed-refs
            - http://host.tld/w3af/.git/objects/info/packs
            ...
        '''
