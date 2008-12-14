'''
ssi.py

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

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.data.fuzzer.fuzzer import createMutants
from core.controllers.w3afException import w3afException

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

import re


class ssi(baseAuditPlugin):
    '''
    Find server side inclusion vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Internal variables
        self._fuzzable_requests = []

    def audit(self, freq ):
        '''
        Tests an URL for server side inclusion vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'ssi plugin is testing: ' + freq.getURL() )
        
        # Used in end()
        self._fuzzable_requests.append( freq )
        
        oResponse = self._sendMutant( freq , analyze=False ).getBody()
        ssi_strings = self._get_ssi_strings()
        mutants = createMutants( freq , ssi_strings, oResponse=oResponse )
            
        for mutant in mutants:
            if self._hasNoBug( 'ssi', 'ssi', mutant.getURL() , mutant.getVar() ):
                # Only spawn a thread if the mutant has a modified variable
                # that has no reported bugs in the kb
                targs = (mutant,)
                self._tm.startFunction( target=self._sendMutant, args=targs, ownerObj=self )
        
        
    def _get_ssi_strings( self ):
        '''
        This method returns a list of server sides to try to include.
        
        @return: A string, see above.
        '''
        local_files = []
        local_files.append("<!--#include file=\"/etc/passwd\"-->")   
        local_files.append("<!--#include file=\"C:\\boot.ini\"-->")
        
        ### TODO: Add mod_perl ssi injection support
        #local_files.append("<!--#perl ")
        
        return local_files
    
    def _analyzeResult( self, mutant, response ):
        '''
        Analyze the result of the previously sent request.
        @return: None, save the vuln to the kb.
        '''
        ssi_error_list = self._find_file( response )
        for ssi_error in ssi_error_list:
            if not re.search( ssi_error, mutant.getOriginalResponseBody(), re.IGNORECASE ):
                v = vuln.vuln( mutant )
                v.setName( 'Server side include vulnerability' )
                v.setSeverity(severity.HIGH)
                v.setDesc( 'Server Side Include was found at: ' + mutant.foundAt() )
                v.setId( response.id )
                kb.kb.append( self, 'ssi', v )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        
        for fr in self._fuzzable_requests:
            self._sendMutant( fr )
            # The _analyzeResult is called and "permanent" SSI's are saved there to the kb
            # Example where this works:
            '''
            Say you have a "guestbook" (a CGI application that allows visitors to leave messages
            for everyone to see) on a server that has SSI enabled. Most such guestbooks around
            the Net actually allow visitors to enter HTML code as part of their comments. Now, 
            what happens if a malicious visitor decides to do some damage by entering the following:

            <--#exec cmd="/bin/rm -fr /"--> 

            If the guestbook CGI program was designed carefully, to strip SSI commands from the
            input, then there is no problem. But, if it was not, there exists the potential for a
            major headache!
            '''
            
        self.printUniq( kb.kb.getData( 'ssi', 'ssi' ), 'VAR' )
            
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
        
    def _find_file( self, response ):
        '''
        This method finds out if the server side has been successfully included in 
        the resulting HTML.
        
        @parameter response: The HTTP response object
        @return: A list of errors found on the page
        '''
        res = []
        for file_pattern in self._get_file_patterns():
            match = re.search( file_pattern, response.getBody() , re.IGNORECASE )
            if  match:
                msg = 'Found server side include. The section where the file is included is (only'
                msg += ' a fragment is shown): "' + response.getBody()[match.start():match.end()]
                msg += '". The error was found on response with id ' + str(response.id) + '.'
                om.out.information(msg)
                res.append(file_pattern)
        return res
    
    def _get_file_patterns(self):
        '''
        @return: A list of strings to find in the resulting HTML in order to check for server side includes.
        '''
        file_patterns = []
        file_patterns.append("root:x:0:0:")  
        file_patterns.append("daemon:x:1:1:")
        file_patterns.append(":/bin/bash")
        file_patterns.append(":/bin/sh")
        file_patterns.append("\\[boot loader\\]")
        file_patterns.append("default=multi\\(")
        file_patterns.append("\\[operating systems\\]")
        return file_patterns
        
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
        This plugin finds server side include (SSI) vulnerabilities.
        '''
