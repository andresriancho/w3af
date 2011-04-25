'''
directoryIndexing.py

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

from core.data.bloomfilter.pybloom import ScalableBloomFilter

import re


class directoryIndexing(baseGrepPlugin):
    '''
    Grep every response for directory indexing problems.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        self._already_visited = ScalableBloomFilter()
        
        # Added performance by compiling all the regular expressions
        # before using them. The setup time of the whole plugin raises,
        # but the execution time is lowered *a lot*.
        self._compiled_regex_list = [ re.compile(regex, re.IGNORECASE | re.DOTALL) for regex in self._get_indexing_regex() ]

    def grep(self, request, response):
        '''
        Plugin entry point, search for directory indexing.
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        if response.getURL().getDomainPath() in self._already_visited:
            # Already worked for this URL, no reason to work twice
            return
        
        else:
            # Save it,
            self._already_visited.add( response.getURL().getDomainPath() )
            
            # Work,
            if response.is_text_or_html():
                html_string = response.getBody()
                for indexing_regex in self._compiled_regex_list:
                    if indexing_regex.search( html_string ):
                        v = vuln.vuln()
                        v.setPluginName(self.getName())
                        v.setURL( response.getURL() )
                        msg = 'The URL: "' + response.getURL() + '" has a directory '
                        msg += 'indexing vulnerability.'
                        v.setDesc( msg )
                        v.setId( response.id )
                        v.setSeverity(severity.LOW)
                        path = response.getURL().getPath()
                        v.setName( 'Directory indexing - ' + path )
                        
                        kb.kb.append( self , 'directory' , v )
                        break
    
    def setOptions( self, OptionList ):
        pass
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def _get_indexing_regex(self):
        '''
        @return: A list of the regular expression strings, in order to be compiled in __init__
        '''
        dir_indexing_regexes = []
        ### TODO: verify if I need to add more values here, IIS !!!
        dir_indexing_regexes.append("<title>Index of /") 
        dir_indexing_regexes.append('<a href="\\?C=N;O=D">Name</a>') 
        dir_indexing_regexes.append("Last modified</a>")
        dir_indexing_regexes.append("Parent Directory</a>")
        dir_indexing_regexes.append("Directory Listing for")
        dir_indexing_regexes.append("<TITLE>Folder Listing.")
        dir_indexing_regexes.append('<table summary="Directory Listing" ')
        dir_indexing_regexes.append("- Browsing directory ")
        dir_indexing_regexes.append('">\\[To Parent Directory\\]</a><br><br>') # IIS 6.0 and 7.0
        dir_indexing_regexes.append('<A HREF=".*?">.*?</A><br></pre><hr></body></html>') # IIS 5.0
        return dir_indexing_regexes
        
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.printUniq( kb.kb.getData( 'directoryIndexing', 'directory' ), 'URL' )
            
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
        This plugin greps every response directory indexing problems.
        '''
