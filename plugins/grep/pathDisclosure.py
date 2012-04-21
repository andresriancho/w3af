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

import re


class pathDisclosure(baseGrepPlugin):
    '''
    Grep every page for traces of path disclosure vulnerabilities.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        # Internal variables
        self._already_added = []
        
        # Compile all regular expressions now
        self._compiled_regexes = {}
        self._compile_regex()
        
    def _compile_regex(self):
        '''
        @return: None, the result is saved in self._path_disc_regex_list
        '''
        #
        #    I tried to enhance the performance of this plugin by putting
        #    all the regular expressions in one (1|2|3|4...|N)
        #    That gave no visible result.
        #
        for path_disclosure_string in self._get_path_disclosure_strings():
            regex_string = '('+path_disclosure_string + '.*?)[^A-Za-z0-9\._\-\\/\+~]'
            regex = re.compile( regex_string,  re.IGNORECASE)
            self._compiled_regexes[ path_disclosure_string ] = regex
            
    def _potential_disclosures(self, html_string ):
        '''
        Taking into account that regular expressions are slow, we first
        apply this function to check if the HTML string has potential
        path disclosures.

        With this performance enhancement we reduce the plugin run time
        to 1/8 of the time in cases where no potential disclosures are found,
        and around 1/3 when potential disclosures *are* found. 
        
        @return: A list of the potential path disclosures
        '''
        potential_disclosures = []
        
        for path_disclosure_string in self._get_path_disclosure_strings():
            if path_disclosure_string in html_string:
                potential_disclosures.append( path_disclosure_string )
            
        return potential_disclosures

    def grep(self, request, response):
        '''
        Identify the path disclosure vulnerabilities.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None, the result is saved in the kb.
        
        >>> from core.data.parsers.urlParser import url_object
        >>> from core.data.request.fuzzableRequest import fuzzableRequest as fuzzableRequest
        >>> from core.data.url.httpResponse import httpResponse as httpResponse
        >>> u = url_object('http://www.w3af.com/')
        >>> req = fuzzableRequest(u, method='GET')
        >>> pd = pathDisclosure()
        
        >>> res = httpResponse(200, 'header body footer' , {'Content-Type':'text/html'}, u, u)
        >>> pd.grep( req, res )
        >>> kb.kb.getData('pathDisclosure', 'pathDisclosure')
        []

        >>> res = httpResponse(200, 'header /etc/passwd footer' , {'Content-Type':'text/html'}, u, u)
        >>> pd.grep( req, res )
        >>> kb.kb.getData('pathDisclosure', 'pathDisclosure')[0]['path']
        u'/etc/passwd'
        '''
        if response.is_text_or_html():
            
            html_string = response.getBody()
            
            for potential_disclosure in self._potential_disclosures( html_string ):
                
                path_disc_regex = self._compiled_regexes[ potential_disclosure ]
                match_list = path_disc_regex.findall( html_string  )

                # Decode the realurl
                realurl = response.getURL().urlDecode()

                
                #   Sort by the longest match, this is needed for filtering out some false positives
                #   please read the note below.
                match_list.sort(self._longest)
                
                for match in match_list:

                    # This if is to avoid false positives
                    if not request.sent( match ) and not \
                    self._attr_value( match, html_string ):
                        
                        # Check for dups
                        if (realurl, match) in self._already_added:
                            continue
                        
                        #   There is a rare bug also, which is triggered in cases like this one:
                        #
                        #   >>> import re
                        #   >>> re.findall('/var/www/.*','/var/www/foobar/htdocs/article.php')
                        #   ['/var/www/foobar/htdocs/article.php']
                        #   >>> re.findall('/htdocs/.*','/var/www/foobar/htdocs/article.php')
                        #   ['/htdocs/article.php']
                        #   >>> 
                        #
                        #   What I need to do here, is to keep the longest match.
                        for realurl_added, match_added in self._already_added:
                            if match_added.endswith( match ):
                                break
                        else:
                        
                            #   Note to self: I get here when "break" is NOT executed.
                            #   It's a new one, report!
                            self._already_added.append( (realurl, match) )
                            
                            v = vuln.vuln()
                            v.setPluginName( self.getName() )
                            v.setURL( realurl )
                            v.setId( response.id )
                            msg = 'The URL: "' + v.getURL() + '" has a path disclosure '
                            msg += 'vulnerability which discloses: "' + match  + '".'
                            v.setDesc( msg )
                            v.setSeverity(severity.LOW)
                            v.setName( 'Path disclosure vulnerability' )
                            v['path'] = match
                            v.addToHighlight( match )
                            kb.kb.append( self, 'pathDisclosure', v )
        
        self._update_KB_path_list()
    
    def _longest(self, a, b):
        '''
        @parameter a: A string.
        @parameter a: Another string.
        @return: The longest string.
        '''
        return cmp(len(a), len(b))
    
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
    
    def _update_KB_path_list( self ):
        '''
        If a path disclosure was found, I can create a list of full paths to all URLs ever visited.
        This method updates that list.
        '''
        path_disc_vulns = kb.kb.getData( 'pathDisclosure', 'pathDisclosure' ) 
        if len( path_disc_vulns ) == 0:
            # I can't calculate the list !
            pass
        else:
            # Init the kb variables
            kb.kb.save( self, 'listFiles', [] )
            
            # Note that this list is recalculated every time a new page is accesed
            # this is goood :P
            url_list = kb.kb.getData( 'urls', 'url_objects' )
            
            # Now I find the longest match between one of the URLs that w3af has
            # discovered, and one of the path disclosure strings that this plugin has
            # found. I use the longest match because with small match_list I have more
            # probability of making a mistake.
            longest_match = ''
            longest_path_disc_vuln = None
            for path_disc_vuln in path_disc_vulns:
                for url in url_list:
                    path_and_file = url.getPath()

                    if path_disc_vuln['path'].endswith( path_and_file ):
                        if len(longest_match) < len(path_and_file):
                            longest_match = path_and_file
                            longest_path_disc_vuln = path_disc_vuln
                        
            # Now I recalculate the place where all the resources are in disk, all this
            # is done taking the longest_match as a reference, so... if we don't have a
            # longest_match, then nothing is actually done
            if longest_match:
                
                # Get the webroot
                webroot = longest_path_disc_vuln['path'].replace( longest_match, '' )
                
                #
                #   This if fixes a strange case reported by Olle
                #           if webroot[0] == '/':
                #           IndexError: string index out of range
                #   That seems to be because the webroot == ''
                #
                if webroot:
                    kb.kb.save( self, 'webroot', webroot )
                    
                    # Check what path separator we should use (linux / windows)
                    if webroot[0] == '/':
                        path_sep = '/'
                    else:
                        # windows
                        path_sep = '\\'
                    
                    # Create the remote locations
                    remote_locations = []
                    for url in url_list:
                        remote_path = url.getPath().replace('/', path_sep)
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
        inform = kb.kb.getData( 'pathDisclosure', 'pathDisclosure' )
        
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
            om.out.information( 'The URL: "' + url + '" has the following path disclosure problems:' )
            for path in tmp[ url ]:
                to_print = '    - ' + path + ' . Found in request with'
                
                list_of_id_list = ids[ path ]
                complete_list = []
                for list_of_id in list_of_id_list:
                    complete_list.extend(list_of_id)
                
                complete_list = list( set( complete_list ) )
                if len(complete_list)==1:
                    to_print += ' id ' + str( complete_list[0] ) + '.'
                else:
                    to_print += ' ids ' + str( complete_list )
                om.out.information( to_print )

    def _get_path_disclosure_strings(self):
        '''
        Return a list of regular expressions to be tested.
        '''
        
        path_disclosure_strings = []
        #path_disclosure_strings.append(r"file:///?[A-Z]\|")
        path_disclosure_strings.extend( get_common_directories() )
        return path_disclosure_strings

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return []
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page for path disclosure vulnerabilities like:
        
            - C:\\www\\files\...
            - /var/www/htdocs/...
            
        The results are saved to the KB, and used by all the plugins that need to know the location
        of a file inside the remote web server.
        '''
