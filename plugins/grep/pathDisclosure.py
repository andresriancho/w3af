'''
pathDisclosure.py

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

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity
from core.data.constants.common_directories import get_common_directories

import core.data.parsers.urlParser as urlParser
import re


class pathDisclosure(baseGrepPlugin):
    '''
    Grep every page for traces of path disclosure problems.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._url_list = []
        
        # Compile all regular expressions now
        self._path_disc_regex_list = []
        self._compile_regex()
        
    def _compile_regex(self):
        '''
        @return: None, the result is saved in self._path_disc_regex_list
        '''
        for path_disclosure_string in self._get_path_disclosure_strings():
            regex_string = '('+path_disclosure_string + '.*?)[:|\'|"|<|\n|\r|\t]'
            regex = re.compile( regex_string,  re.IGNORECASE)
            self._path_disc_regex_list.append(regex)

    def grep(self, request, response):
        '''
        Identify the path disclosure vulnerabilities.
        
        @return: None, the result is saved in the kb.
        '''
        if response.is_text_or_html():
            # Decode the realurl
            realurl = urlParser.urlDecode( response.getURL() )
            
            html_string = response.getBody()
            for path_disc_regex in self._path_disc_regex_list:
                match_list = path_disc_regex.findall( html_string  )
                
                for match in match_list:
                   
                    # This if is to avoid false positives
                    if not self._wasSent( request, match ) and not \
                    self._attr_value( match, html_string ):
                        
                        v = vuln.vuln()
                        v.setURL( realurl )
                        v.setId( response.id )
                        msg = 'The URL: "' + v.getURL() + '" has a path disclosure '
                        msg += 'vulnerability which discloses: "' + match  + '".'
                        v.setDesc( msg )
                        v.setSeverity(severity.LOW)
                        v.setName( 'Path disclosure vulnerability' )
                        v['path'] = match
                        kb.kb.append( self, 'pathDisclosure', v )
        
        self._update_KB_path_list( response.getURL() )
    
    def _attr_value(self, path_disclosure_string, response_body ):
        '''
        This method was created to remove some false positives.
        
        @return: True if path_disclosure_string is the value of an attribute inside a tag.
        
        Examples:
            path_disclosure_string = '/home/image.png'
            response_body = '....<img src="/home/image.png">...'
            return: True
            
            path_disclosure_string = '/home/image.png'
            response_body = '...<b>Error while processing /home/image.png</b>...'
            return: False
        '''
        regex_res = re.findall('<.+?(["|\']'+ re.escape(path_disclosure_string) +'["|\']).*?>', response_body)
        in_attr = path_disclosure_string in regex_res
        return in_attr
    
    def _update_KB_path_list( self, url ):
        '''
        If a path disclosure was found, I can create a list of full paths to all URLs ever visited.
        This method updates that list.
        
        @parameter url: The URL where the path disclosure was found.
        '''
        self._url_list.append( url )
        
        path_disc_vulns = kb.kb.getData( 'pathDisclosure', 'pathDisclosure' ) 
        if len( path_disc_vulns ) == 0:
            # I cant calculate the list !
            pass
        else:
            # Init the kb variables
            kb.kb.save( self, 'listFiles', [] )
            
            # Note that this list is recalculated every time a new page is accesed
            # this is goood :P
            url_list = kb.kb.getData( 'urls', 'urlList' )
            
            # Now I find the longest match between one of the URLs that w3af has
            # discovered, and one of the path disclosure strings that this plugin has
            # found. I use the longest match because with small match_list I have more
            # probability of making a mistake.
            longest_match = ''
            longest_path_disc_vuln = None
            for path_disc_vuln in path_disc_vulns:
                for url in url_list:
                    path_and_file = urlParser.getPath( url )

                    if path_disc_vuln['path'].endswith( path_and_file ):
                        if len(longest_match) < len(path_and_file):
                            longest_match = path_and_file
                            longest_path_disc_vuln = path_disc_vuln
                        
            # Now I recalculate the place where all the resources are in disk, all this
            # is done taking the longest_match as a reference, so... if we don't have a
            # longest_match, then nothing is actually done
            if longest_match:
                
                # Get the webroot
                webroot = longest_path_disc_vuln['path'].replace( path_and_file, '' )
                
                # Check what path separator we should use
                if webroot[0] == '/':
                    path_sep = '/'
                else:
                    # windows
                    path_sep = '\\'
                
                # Create the remote locations
                remote_locations = []
                for url in url_list:
                    remote_path = urlParser.getPath( url ).replace('/', path_sep)
                    remote_locations.append( webroot + remote_path )
                remote_locations = list( set( remote_locations ) )
                kb.kb.save( self, 'listFiles', remote_locations )
        
    def setOptions( self, OptionList ):
        pass
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        inform = []
        for v in kb.kb.getData( 'pathDisclosure', 'pathDisclosure' ):
            inform.append( v )
        
        tmp = {}
        ids = {}
        for v in inform:
            if v.getURL() in tmp.keys():
                tmp[ v.getURL() ].append( v['path'] )
            else:
                tmp[ v.getURL() ] = [ v['path'], ]
                                
            if v['path'] in ids.keys():
                ids[ v['path'] ].append( v.getId() )
            else:
                ids[ v['path'] ] = [ v.getId(), ]
        
        # Avoid duplicates
        for url in tmp.keys():
            tmp[ url ] = list( set( tmp[ url ] ) )
        
        for url in tmp.keys():
            om.out.information( 'The URL: ' + url + ' has the following path disclosure problems:' )
            for path in tmp[ url ]:
                toPrint = '- ' + path + ' . Found in request id\'s: '
                toPrint += str( list( set( ids[ path ] ) ) )
                om.out.information( toPrint )

    def _get_path_disclosure_strings(self):
        '''
        Return a list of regular expressions to be tested.
        '''
        
        path_disclosure_strings = []
        path_disclosure_strings.append(r"[A-Z]:\\")
        path_disclosure_strings.append(r"file:///?[A-Z]\|")
        path_disclosure_strings.extend( get_common_directories() )
        return path_disclosure_strings

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
        This plugin greps every page for path disclosure vulnerabilities like:
        
            - C:\www\files\...
            - /var/www/htdocs/...
            
        The results are saved to the KB, and used by all the plugins that need to know the location
        of a file inside the remote web server.
        '''
