'''
find_dvcs.py

Copyright 2011 Adam Baldwin

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

from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.w3afException import w3afException
from core.data.bloomfilter.bloomfilter import scalable_bloomfilter


class find_dvcs(CrawlPlugin):
    '''
    Find GIT, Mercurial (HG), and Bazaar (BZR) repositories

    @author: Adam Baldwin (adam_baldwin@ngenuity-is.com)
    '''

    def __init__(self):
        CrawlPlugin.__init__(self)
        
        # Internal variables
        self._analyzed_dirs = scalable_bloomfilter()
        self._compile_DVCS_RE()

    def crawl(self, fuzzable_request ):
        '''
        For every directory, fetch a list of files and analyze the response
        using regex.
        
        @parameter fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''
        domain_path = fuzzable_request.getURL().getDomainPath()
        
        if domain_path not in self._analyzed_dirs:
            self._analyzed_dirs.add( domain_path )

            test_generator = self._url_generator( domain_path )
            
            self._tm.threadpool.map_multi_args(self._send_and_check, test_generator)
    
    def _send_and_check(self, repo_url, regular_expression, repo):
        try:
            response = self._uri_opener.GET( repo_url, cache=True )
        except w3afException:
            om.out.debug('Failed to GET '+repo+' file: "' + repo_url + '"')
        else:
            # Check pattern
            f = StringIO.StringIO(response.getBody())
            for line in f:
                if regular_expression.match(line):
                    v = vuln.vuln()
                    v.setPluginName(self.getName())
                    v.setId( response.id )
                    v.setName( 'Possible '+repo+' repository found' )
                    v.setSeverity(severity.LOW)
                    v.setURL( response.getURL() )
                    msg = ('A %s repository file was found at: "%s"; this could'
                           ' indicate that a %s repo is accessible. You might'
                           ' be able to download the Web application source code.')
                    v.setDesc( msg % (repo, v.getURL(), repo) )
                    kb.kb.append( self, repo.upper(), v )
                    om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
                    for fr in self._create_fuzzable_requests( response ):
                        self.output_queue.put(fr)
    
    def _url_generator(self, domain_path):
        for repo in self._compiled_dvcs_info.keys():
            relative_url = self._compiled_dvcs_info[repo]['filename']
            regular_expression = self._compiled_dvcs_info[repo]['re']
            repo_url = domain_path.urlJoin(relative_url)
            yield repo_url, regular_expression, repo
    
    def _compile_DVCS_RE( self ):
        '''
        Compile the regular expressions. This is done at the beginning,
        in order to save CPU power.

        @return: None, the result is saved in "self._compiled_dvcs_info".
        '''
        self._compiled_dvcs_info = {} 
        self._compiled_dvcs_info['git'] = {} 
        self._compiled_dvcs_info['hg'] = {} 
        self._compiled_dvcs_info['bzr'] = {} 

        self._compiled_dvcs_info['git']['re'] = re.compile('^ref: refs/')
        self._compiled_dvcs_info['git']['filename'] = '.git/HEAD'

        self._compiled_dvcs_info['hg']['re'] = re.compile('^revlogv1')
        self._compiled_dvcs_info['hg']['filename'] = '.hg/requires'

        self._compiled_dvcs_info['bzr']['re'] = re.compile('^This\sis\sa\sBazaar')
        self._compiled_dvcs_info['bzr']['filename'] = '.bzr/README'

    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
    	This plugin search for evidence of git, hg or bzr metadata in a directory. 
        For example, if the input is:
            - http://host.tld/w3af/index.php
            
        The plugin will perform requests to:
            - http://host.tld/w3af/.git/HEAD
            - http://host.tld/w3af/.hg/requires
            - http://host.tld/w3af/.bzr/README
        '''
