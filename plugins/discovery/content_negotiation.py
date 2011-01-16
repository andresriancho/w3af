'''
content_negotiation.py

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

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from core.controllers.w3afException import w3afRunOnce

from core.data.bloomfilter.pybloom import ScalableBloomFilter

import os
import re


class content_negotiation(baseDiscoveryPlugin):
    '''
    Use content negotiation to find new resources.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # User configured parameters
        self._wordlist = 'plugins' + os.path.sep + 'discovery' + os.path.sep + 'content_negotiation'
        self._wordlist += os.path.sep + 'common_filenames.db'
        
        # Internal variables
        self._exec = True
        self._already_tested_dir = ScalableBloomFilter()
        self._already_tested_resource = ScalableBloomFilter()
        self._is_vulnerable_result = None
        self._to_bruteforce = []
        # I want to try 3 times to see if the remote host is vulnerable
        # detection is not thaaat accurate!
        self._tries_left = 3

    def discover(self, fuzzableRequest ):
        '''
        1- Check if HTTP server is vulnerable
        2- Exploit using fuzzableRequest
        3- Perform bruteforce for each new directory
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains 
                                                    (among other things) the URL to test.
        '''
        if not self._exec :
            # This will remove the plugin from the discovery plugins to be runned.
            # This is true only when the remote web server is not vulnerable
            raise w3afRunOnce()
            
        else:
            
            if self._is_vulnerable( fuzzableRequest ) is None:
                # I can't say if it's vulnerable or not (yet), save the current directory to be
                # included in the bruteforcing process, and return.
                self._to_bruteforce.append(fuzzableRequest.getURL())
                return []
            
            elif self._is_vulnerable( fuzzableRequest ) == False:
                # Not vulnerable, nothing else to do.
                self._exec = False
                return []
                
            else:
                # Happy, happy, joy!
                # Now we can test if we find new resources!
                new_resources = self._find_new_resources( fuzzableRequest )
                
                # and we can also perform a bruteforce:
                self._to_bruteforce.append(fuzzableRequest.getURL())
                bruteforce_result = self._bruteforce()
                
                result = []
                result.extend( new_resources )
                result.extend( bruteforce_result )
                
                return result
    
    def _find_new_resources(self, fuzzableRequest):
        '''
        Based on a request like http://host.tld/backup.php , this method will find
        files like backup.zip , backup.old, etc. Using the content negotiation technique.
        
        @return: A list of new fuzzable requests.
        '''
        result = []
        
        # Get the file name
        filename = fuzzableRequest.getURL().getFileName()
        if filename == '':
            # We need a filename to work with!
            return []
        else:
            # Ok, we have a file name.
            # The thing here is that I've found that if these files exist in the directory:
            # - backup.asp.old
            # - backup.asp
            #
            # And I request "/backup" , then both are returned. So I'll request the "leftmost"
            # filename.
            filename = filename.split('.')[0]
            
            # Now I simply perform the request:
            alternate_resource = fuzzableRequest.getURL().urlJoin(filename)
            original_headers = fuzzableRequest.getHeaders()
            
            if alternate_resource not in self._already_tested_resource:
                self._already_tested_resource.add( alternate_resource )

                alternates = self._request_and_get_alternates( alternate_resource, original_headers)
           
                # And create the new fuzzable requests
                result = self._create_new_fuzzablerequests( fuzzableRequest.getURL(), alternates )
        
        return result
    
    def _bruteforce(self):
        '''
        Use some common words to bruteforce file names and find new resources.
        This process is done only once for every new directory.
        
        @return: A list of new fuzzable requests.
        '''
        result = []
        to_analyze = []
        
        # Create the list of directories to analyze:
        for url in self._to_bruteforce:
            directories = url.getDirectories()
            
            for directory_url in directories:
                if directory_url not in to_analyze and directory_url not in self._already_tested_dir:
                    to_analyze.append( directory_url )
        
        # Really bruteforce:
        for directory_url in to_analyze:
            self._already_tested_dir.add( directory_url )
            
            for word in file(self._wordlist):
                alternate_resource = directory_url.urlJoin( word.strip() )
                alternates = self._request_and_get_alternates( alternate_resource, {})
                result = self._create_new_fuzzablerequests( directory_url,  alternates )
        
        # I already analyzed them, zeroing.
        self._to_bruteforce = []
        
        return result
    
    def _request_and_get_alternates(self, alternate_resource, headers):
        '''
        Performs a request to an alternate resource, using the fake accept trick in order to
        retrieve the list of alternates, which is then returned.
        
        @return: A list of strings containing the alternates.
        '''
        headers['Accept'] = 'w3af/bar'
        response = self._urlOpener.GET( alternate_resource, headers = headers )
        
        # And I parse the result
        if 'alternates' in response.getLowerCaseHeaders():
            alternates = response.getLowerCaseHeaders()['alternates']
            
            # An alternates header looks like this:
            # alternates: {"backup.php.bak" 1 {type application/x-trash} {length 0}}, 
            #                   {"backup.php.old" 1 {type application/x-trash} {length 0}},
            #                   {"backup.tgz" 1 {type application/x-gzip} {length 0}},
            #                   {"backup.zip" 1 {type application/zip} {length 0}}
            #
            # All in the same line.
            return re.findall( '"(.*?)"', alternates )
        
        else:
            # something failed
            return []

    def _create_new_fuzzablerequests(self, base_url, alternates):
        '''
        With a list of alternate files, I create new fuzzable requests
        
        @parameter base_url: http://host.tld/some/dir/
        @parameter alternates: ['backup.old', 'backup.asp']
        
        @return: A list of fuzzable requests.
        '''
        result = []
        for alternate in alternates:
            # Get the new resource
            full_url = base_url.urlJoin(alternate)
            response = self._urlOpener.GET( full_url )
                
            result.extend( self._createFuzzableRequests( response ) )
            
        return result

    def _is_vulnerable(self, fuzzableRequest):
        '''
        Checks if the remote website is vulnerable or not. Saves the result in
        self._is_vulnerable_result , because we want to perform this test only once.
        
        @return: True if vulnerable.
        '''
        if self._is_vulnerable_result is not None:
            # The test was already performed, we return the old response
            return self._is_vulnerable_result
            
        else:
            # We perform the test, for this we need a URL that has a filename, URL's
            # that don't have a filename can't be used for this.
            filename = fuzzableRequest.getURL().getFileName()
            if filename == '':
                return None
        
            filename = filename.split('.')[0]
            
            # Now I simply perform the request:
            alternate_resource = fuzzableRequest.getURL().urlJoin(filename)
            headers = fuzzableRequest.getHeaders()
            headers['Accept'] = 'w3af/bar'
            response = self._urlOpener.GET( alternate_resource, headers = headers )
            
            if 'alternates' in response.getLowerCaseHeaders():
                # Even if there is only one file, with an unique mime type, the content negotiation
                # will return an alternates header. So this is pretty safe.
                
                # Save the result internally
                self._is_vulnerable_result = True
                
                # Save the result as an info in the KB, for the user to see it:
                i = info.info()
                i.setPluginName(self.getName())
                i.setName('HTTP Content Negotiation enabled')
                i.setURL( response.getURL() )
                i.setMethod( 'GET' )
                desc = 'HTTP Content negotiation is enabled in the remote web server. This '
                desc += ' could be used to bruteforce file names and find new resources.'
                i.setDesc( desc )
                i.setId( response.id )
                kb.kb.append( self, 'content_negotiation', i )
                om.out.information( i.getDesc() )
            else:
                om.out.information('The remote Web server has Content Negotiation disabled.')
                
                # I want to perform this test a couple of times... so I only return False
                # if that "couple of times" is empty
                self._tries_left -= 1
                if self._tries_left == 0:
                    # Save the FALSE result internally
                    self._is_vulnerable_result = False
                else:
                    # None tells the plugin to keep trying with the next URL
                    return None
            
            # return the result =)
            return self._is_vulnerable_result
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Wordlist to use in the file name bruteforcing process.'
        o1 = option('wordlist', self._wordlist , d1, 'string')
        
        ol = optionList()
        ol.add(o1)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        wordlist = optionsMap['wordlist'].getValue()
        if os.path.exists( wordlist ):
            self._wordlist = wordlist

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return ['discovery.webSpider']
        
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin uses HTTP content negotiation to find new resources.
        
        The plugin has three distinctive phases:

            - Idenfity if the web has content negotiation enabled.
            - For every resource found by any other plugin, perform a request to find new related
                resources. For example, if another plugin finds "index.php", this plugin will perform a
                request for "/index" with customized headers that will return a list of all files that have
                "index" as the file name.
            - Perform a brute force attack in order to find new resources.
        
        One configurable parameter exists:
            - wordlist: The wordlist to be used in the bruteforce process.
        
        As far as I can tell, the first reference to this technique was written by Stefano Di Paola
        in his blog (http://www.wisec.it/sectou.php?id=4698ebdc59d15).
        '''
