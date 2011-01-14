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

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.w3afException import w3afException

from core.controllers.coreHelpers.fingerprint_404 import is_404
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity
import re
import StringIO


class findGit(baseDiscoveryPlugin):
    '''
    Find GIT repositories
    @author: Adam Baldwin (adam_baldwin@ngenuity-is.com)
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._analyzed_dirs = []
        self._fuzzable_requests_to_return = []
        self._compile_gitRE()

    def discover(self, fuzzableRequest ):
        '''
        For every directory, fetch a list of files and analyze the response using regex.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        domain_path = fuzzableRequest.getURL().getDomainPath()
        self._fuzzable_requests_to_return = []
        
        if domain_path not in self._analyzed_dirs:
            self._analyzed_dirs.append( domain_path )

            #
            #   First we check if the .git/HEAD file exists
            #
            relative_url, regular_expression = self._compiled_git_info[0]
            git_url = domain_path.urlJoin(relative_url)
            try:
                response = self._urlOpener.GET( git_url, useCache=True )
            except w3afException:
                om.out.debug('Failed to GET git file: "' + git_url + '"')
            else:
                if not is_404(response):
                    #
                    #   It looks like we have a GIT repository!
                    #
                    for relative_url, regular_expression in self._compiled_git_info:
                        git_url = domain_path.urlJoin(relative_url)
                        targs = (domain_path, git_url, regular_expression)
                        # Note: The .git/HEAD request is only sent once. We use the cache.
                        self._tm.startFunction(target=self._check_if_exists, args=targs, ownerObj=self)         
                    
                    # Wait for all threads to finish
                    self._tm.join( self )
                
            return self._fuzzable_requests_to_return
    
    def _check_if_exists(self, domain_path, git_url, regular_expression):
        '''
        Check if the file exists.
        
        @parameter git_file_url: The URL to check
        '''
        try:
            response = self._urlOpener.GET( git_url, useCache=True )
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
                        kb.kb.append( self, 'GIT', v )
                        om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
                        fuzzable_requests = self._createFuzzableRequests( response )
                        self._fuzzable_requests_to_return.extend( fuzzable_requests )
                    
    def _compile_gitRE( self ):
        '''
        Compile the GIT regular expressions. This is done at the beginning,
        in order to save CPU power.

        @return: None, the result is saved in "self._compiled_git_info".
        '''
        self._compiled_git_info = []
        #
        # don't change the order! the first element is used in a different way
        #
        self._compiled_git_info.append( ['.git/HEAD',re.compile('^ref: refs/')])
        self._compiled_git_info.append( ['.git/info/refs',re.compile('^[a-f0-9]{40}\s+refs/')])
        self._compiled_git_info.append( ['.git/objects/info/packs',re.compile('^P pack-[a-f0-9]{40}\.pack')])
        self._compiled_git_info.append( ['.git/packed-refs',re.compile('^[a-f0-9]{40} refs/')])
        self._compiled_git_info.append( ['.git/refs/heads/master',re.compile('^[a-f0-9]{40}')])

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
