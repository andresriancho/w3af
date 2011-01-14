'''
svnUsers.py

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
from core.data.bloomfilter.pybloom import ScalableBloomFilter

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

import re


class svnUsers(baseGrepPlugin):
    '''
    Grep every response for users of the versioning system.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._already_inspected = ScalableBloomFilter()
        # Add the regex to match something like this:
        #
        #   $Id: lzio.c,v 1.24 2003/03/20 16:00:56 roberto Exp $
        #   $Id: file name, version, timestamp, creator Exp $
        #
        regex = '\$.{1,12}: .*? .*? \d{4}[-/]\d{1,2}[-/]\d{1,2}'
        regex += ' \d{1,2}:\d{1,2}:\d{1,2}.*? (.*?) (Exp )?\$'
        self._regex_list = [ re.compile(regex) ]
        
    def grep(self, request, response):
        '''
        Plugin entry point.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None, all results are saved in the kb.
        '''
        uri = response.getURI()
        if response.is_text_or_html() and uri not in self._already_inspected:

            # Don't repeat URLs
            self._already_inspected.add(uri)

            for regex in self._regex_list:
                for m in regex.findall(response.getBody()):
                    v = vuln.vuln()
                    v.setPluginName(self.getName())
                    v.setURI(uri)
                    v.setId(response.id)
                    msg = 'The URL: "' + uri + '" contains a SVN versioning '
                    msg += 'signature with the username: "' + m[0] + '" .'
                    v.setDesc(msg)
                    v['user'] = m[0]
                    v.setSeverity(severity.LOW)
                    v.setName('SVN user disclosure vulnerability')
                    v.addToHighlight(m[0])
                    kb.kb.append(self, 'users', v)

        
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
        self.printUniq( kb.kb.getData( 'svnUsers', 'users' ), 'URL' )
    
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
        This plugin greps every page for users of the versioning system. Sometimes the HTML pages are
        versioned using CVS or SVN, if the header of the versioning system is saved as a comment in this page,
        the user that edited the page will be saved on that header and will be added to the knowledgeBase.
        '''
